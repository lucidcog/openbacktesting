"""Authenticated loopback API; user source is only evaluated by workers."""

from __future__ import annotations

import asyncio
import json
import secrets
import sys
import threading
import uuid
from contextlib import asynccontextmanager
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from openbacktesting_studio import __version__
from openbacktesting_studio.artifacts import (
    export_container,
    import_container,
    import_portfolio,
    strict_json,
    validate,
)
from openbacktesting_studio.execution.manager import RunManager
from openbacktesting_studio.execution.process import discover, probe
from openbacktesting_studio.host import reports
from openbacktesting_studio.protocol import (
    DataProfile,
    FileWrite,
    Message,
    Preset,
    RunRequest,
    SourceRequest,
)
from openbacktesting_studio.workspace import Workspace, WorkspaceError


class WorkspaceSelection(Message):
    path: str = Field(min_length=1, max_length=4096)


class SessionRequest(Message):
    token: str = Field(min_length=16, max_length=256)


def create_app(
    root: Path | None,
    *,
    origin: str,
    python=sys.executable,
    readonly=False,
    token=None,
    discover_timeout=30,
    viewer=None,
    choose_workspace=False,
):
    location = urlsplit(origin)
    if location.scheme != "http" or location.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Studio requires an HTTP loopback origin")
    workspace = (
        Workspace(root) if root is not None and not readonly and not choose_workspace else None
    )
    environment = (
        probe(python) if not readonly else {"compatible": False, "message": "Read-only viewer"}
    )

    @asynccontextmanager
    async def lifespan(app):
        app.state.manager = (
            RunManager(workspace, python, environment)
            if workspace and environment["compatible"]
            else None
        )
        try:
            yield
        finally:
            if app.state.manager:
                await run_in_threadpool(app.state.manager.close)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.startup_token = token or secrets.token_urlsafe(32)
    app.state.workspace = workspace
    app.state.environment = environment
    app.state.suggested_workspace = str(root or Path.home())
    app.state.workspace_id = uuid.uuid4().hex
    workspace_requests = asyncio.Condition()
    switching = False
    active_requests = 0
    exchange_lock = threading.Lock()
    session = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    cookie = "studio_" + secrets.token_hex(8)

    def error(request, code, message, status, **details):
        return JSONResponse(
            status_code=status,
            content={
                "code": code,
                "message": message,
                "fieldErrors": details.pop("fieldErrors", {}),
                "details": details,
                "requestId": getattr(request.state, "request_id", ""),
            },
        )

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex
        if request.headers.get("host") != location.netloc:
            return error(request, "HostDenied", "Invalid Studio host", 403)
        if request.url.path.startswith("/api/"):
            if request.url.path != "/api/v1/session" or request.method != "POST":
                if not secrets.compare_digest(request.cookies.get(cookie, ""), session):
                    return error(request, "SessionDenied", "A valid local session is required", 403)
                if request.headers.get("x-studio-protocol") != "1":
                    return error(
                        request, "ProtocolMismatch", "Unsupported Studio protocol version", 409
                    )
            if request.method not in {"GET", "HEAD"}:
                if request.headers.get("origin") != origin:
                    return error(request, "OriginDenied", "Invalid request origin", 403)
                if request.url.path != "/api/v1/session" and not secrets.compare_digest(
                    request.headers.get("x-studio-csrf", ""), csrf
                ):
                    return error(request, "CsrfDenied", "Invalid request token", 403)
        nonlocal active_requests
        scoped = request.url.path.startswith("/api/") and request.url.path not in {
            "/api/v1/session",
            "/api/v1/workspace",
            "/api/v1/directories",
            "/api/v1/capabilities",
        }
        if scoped:
            async with workspace_requests:
                if switching:
                    return error(
                        request, "WorkspaceSwitching", "Workspace selection is changing", 409
                    )
                identity = request.headers.get("x-studio-workspace")
                if identity and identity != app.state.workspace_id:
                    return error(
                        request,
                        "WorkspaceChanged",
                        "Workspace changed in another tab; reload Studio",
                        409,
                    )
                if not readonly and workspace is None:
                    return error(
                        request, "WorkspaceRequired", "Choose a workspace directory first", 409
                    )
                active_requests += 1
        try:
            response = await call_next(request)
        finally:
            if scoped:
                async with workspace_requests:
                    active_requests -= 1
                    workspace_requests.notify_all()
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
                "X-Frame-Options": "DENY",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; font-src 'self'; connect-src 'self'; worker-src 'self' blob:; "
                "object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
                "X-Request-ID": request.state.request_id,
            }
        )
        return response

    @app.exception_handler(WorkspaceError)
    async def workspace_error(request, failure):
        return error(request, failure.code, str(failure), failure.status, **failure.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, failure):
        fields = {}
        for item in failure.errors():
            fields.setdefault(".".join(str(part) for part in item["loc"][1:]), []).append(
                item["msg"]
            )
        return error(
            request, "InvalidRequest", "Review the highlighted fields", 422, fieldErrors=fields
        )

    @app.exception_handler(HTTPException)
    async def http_error(request, failure):
        return error(
            request,
            "NotFound" if failure.status_code == 404 else "HttpError",
            str(failure.detail),
            failure.status_code,
        )

    @app.exception_handler(Exception)
    async def internal_error(request, failure):
        return error(
            request,
            "InternalError",
            "The local operation failed; see the host diagnostic",
            500,
            errorType=type(failure).__name__,
        )

    def manager():
        value = getattr(app.state, "manager", None)
        if value is None:
            raise WorkspaceError(
                "InterpreterIncompatible", environment.get("message", "Worker unavailable"), 422
            )
        return value

    def result_directory(run_id):
        if viewer is not None:
            manifest = validate(viewer)
            if manifest.runId != run_id:
                raise WorkspaceError("RunNotFound", "Run does not exist", 404)
            return Path(viewer)
        return manager().result_path(run_id)

    @app.post("/api/v1/session")
    def establish(payload: SessionRequest, request: Request):
        with exchange_lock:
            expected = app.state.startup_token
            if expected is None or not secrets.compare_digest(payload.token, expected):
                return error(
                    request, "SessionDenied", "Launch token is invalid or already used", 403
                )
            app.state.startup_token = None
        response = JSONResponse({"protocolVersion": 1, "csrf": csrf})
        response.set_cookie(cookie, session, httponly=True, samesite="strict", path="/")
        return response

    @app.get("/api/v1/capabilities")
    def capabilities():
        return {
            "protocolVersion": 1,
            "studioVersion": __version__,
            "mode": "view" if readonly else "workspace",
            "workspace": str(workspace.root) if workspace else None,
            "workspaceId": app.state.workspace_id,
            "suggestedWorkspace": app.state.suggested_workspace,
            "interpreter": environment,
            "limits": {
                "fileBytes": workspace.max_file_bytes if workspace else 0,
                "queuedRuns": 8,
                "pageSize": 100,
                "maxPageSize": 1000,
                "chartPoints": 5000,
                "maxChartPoints": 20000,
                "maxChartValues": 1000000,
                "maxChartEvents": 20000,
                "outputBytesPerStream": 1048576,
                "structuredLogBytes": 1048576,
                "importEntries": 20000,
                "importBytes": 512 * 1024 * 1024,
            },
            "capabilities": {
                "edit": workspace is not None,
                "discover": workspace is not None and environment["compatible"],
            },
        }

    @app.get("/api/v1/session")
    def resume_session():
        return {"protocolVersion": 1, "csrf": csrf}

    @app.get("/api/v1/runs")
    def history():
        if viewer is not None:
            value = validate(viewer)
            return {"runs": [{"id": value.runId, "status": value.status, "imported": True}]}
        return {"runs": manager().history()}

    @app.get("/api/v1/runs/{run_id}")
    def run_status(run_id: str):
        if viewer is not None:
            result_directory(run_id)
            return {"id": run_id, "status": "succeeded", "imported": True}
        return manager().get(run_id)

    @app.get("/api/v1/runs/{run_id}/summary")
    def report(run_id: str):
        return reports.summary(result_directory(run_id))

    @app.get("/api/v1/runs/{run_id}/trades")
    def trades(run_id: str, table: str = "closedFragments", offset: int = 0, limit: int = 100):
        return reports.rows(result_directory(run_id), table, offset, limit)

    @app.get("/api/v1/runs/{run_id}/curve")
    def curve(run_id: str, limit: int = 5000):
        return reports.curve(result_directory(run_id), limit)

    @app.get("/api/v1/runs/{run_id}/catalog")
    def catalog(run_id: str):
        path = result_directory(run_id) / "catalog.json"
        if path.is_file():
            return strict_json(path.read_bytes())
        from openbacktesting.portfolio import report_catalog

        return report_catalog()

    @app.get("/api/v1/runs/{run_id}/chart")
    def chart(run_id: str, start: int | None = None, limit: int = 5000, end: int | None = None):
        return reports.chart(result_directory(run_id), start, limit, end)

    @app.get("/api/v1/runs/{run_id}/events")
    def chart_events(run_id: str, start: int, end: int, offset: int = 0, limit: int = 100):
        return reports.events(result_directory(run_id), start, end, offset, limit)

    @app.get("/api/v1/runs/{run_id}/provenance")
    def provenance(run_id: str):
        return validate(result_directory(run_id)).model_dump()

    @app.get("/api/v1/runs/{run_id}/source")
    def snapshot_source(run_id: str, path: str):
        from hashlib import sha256

        from openbacktesting_studio.protocol import relative_path

        try:
            relative_path(path)
        except ValueError as failure:
            raise WorkspaceError("PathDenied", str(failure), 403) from failure
        if viewer is not None:
            base = result_directory(run_id) / "source"
        else:
            record = manager().get(run_id)
            if record["status"] == "succeeded":
                base = result_directory(run_id) / "source"
            else:
                request = strict_json(
                    (manager().runs / run_id / "worker-request.json").read_bytes()
                )
                if path not in request["snapshot"]["files"]:
                    raise WorkspaceError("SourceUnavailable", "No snapshot for this source", 404)
                base = Path(request["snapshot"]["directory"])
        target = base / path
        if (
            not target.is_file()
            or target.is_symlink()
            or not target.resolve().is_relative_to(base.resolve())
            or target.stat().st_size > 2 * 1024 * 1024
        ):
            raise WorkspaceError(
                "SourceUnavailable", "Source was not included or exceeds the editor limit", 404
            )
        raw = target.read_bytes()
        revision = sha256(raw).hexdigest()
        current = None
        if workspace:
            try:
                current = workspace.read(path)["revision"]
            except WorkspaceError:
                pass
        return {
            "path": path,
            "content": raw.decode("utf-8"),
            "revision": revision,
            "currentMatches": current == revision,
        }

    @app.get("/api/v1/runs/{run_id}/logs")
    def logs(run_id: str):
        directory = result_directory(run_id)
        return {
            name: strict_json((directory / f"{name}.json").read_bytes())
            if (directory / f"{name}.json").is_file()
            else None
            for name in ["logs", "stdout", "stderr"]
        }

    @app.get("/api/v1/runs/{run_id}/export")
    def export(run_id: str, source: bool = False, data: bool = False, logs: bool = False):
        import tempfile

        from starlette.background import BackgroundTask

        descriptor, filename = tempfile.mkstemp(suffix=".obstudio")
        import os

        os.close(descriptor)
        export_container(
            result_directory(run_id),
            filename,
            include_source=source,
            include_data=data,
            include_logs=logs,
        )
        return FileResponse(
            filename,
            filename=f"{run_id}.obstudio",
            background=BackgroundTask(Path(filename).unlink),
        )

    if not readonly:
        from openbacktesting_studio.host.optimization import install_optimizer_routes

        install_optimizer_routes(app, manager)
        from openbacktesting_studio.workspace.configuration import ConfigurationStore

        configuration = ConfigurationStore(workspace.root) if workspace else None

        def directory(path):
            try:
                result = Path(path).expanduser().resolve(strict=True)
                if not result.is_dir():
                    raise ValueError("Not a directory")
                return result
            except (OSError, ValueError) as failure:
                raise WorkspaceError(
                    "DirectoryUnavailable", "Choose an existing accessible directory", 422
                ) from failure

        @app.get("/api/v1/directories")
        def directories(path: str | None = None):
            selected = directory(path or app.state.suggested_workspace)
            try:
                children = sorted(
                    entry.name
                    for entry in selected.iterdir()
                    if not entry.name.startswith(".") and entry.is_dir() and not entry.is_symlink()
                )
            except OSError as failure:
                raise WorkspaceError(
                    "DirectoryUnavailable", "Directory cannot be read", 403
                ) from failure
            return {"path": str(selected), "parent": str(selected.parent), "directories": children}

        @app.put("/api/v1/workspace")
        async def select_workspace(payload: WorkspaceSelection):
            nonlocal workspace, configuration, switching
            selected = directory(payload.path)
            async with workspace_requests:
                if switching:
                    raise WorkspaceError(
                        "WorkspaceSwitching", "Workspace selection is changing", 409
                    )
                switching = True
                try:
                    await workspace_requests.wait_for(lambda: active_requests == 0)
                except BaseException:
                    switching = False
                    workspace_requests.notify_all()
                    raise
            try:
                if workspace and selected == workspace.root:
                    return capabilities()
                old = getattr(app.state, "manager", None)
                if old and (
                    old.optimizer.active
                    or any(
                        row["status"] not in {"succeeded", "failed", "cancelled"}
                        for row in old.history()
                    )
                ):
                    raise WorkspaceError(
                        "WorkspaceBusy",
                        "Finish or cancel active runs before switching directories",
                        409,
                    )
                new_workspace = Workspace(selected)
                new_configuration = ConfigurationStore(selected)
                new_manager = (
                    await run_in_threadpool(RunManager, new_workspace, python, environment)
                    if environment["compatible"]
                    else None
                )
                try:
                    if old:
                        await run_in_threadpool(old.close)
                except Exception:
                    if new_manager:
                        await run_in_threadpool(new_manager.close)
                    raise
                workspace, configuration = new_workspace, new_configuration
                app.state.workspace = workspace
                app.state.manager = new_manager
                app.state.workspace_id = uuid.uuid4().hex
                return capabilities()
            finally:
                async with workspace_requests:
                    switching = False
                    workspace_requests.notify_all()

        @app.get("/api/v1/runs/{run_id}/workspace-match")
        def workspace_match(run_id: str):
            from hashlib import sha256
            from pathlib import PurePosixPath

            record = manager().get(run_id)
            expected = record.get("sourceFiles")
            if not expected:
                return {"runId": run_id, "matches": None, "changed": []}
            changed = []
            for name, digest in expected.items():
                try:
                    if sha256(workspace.read_bytes(name)[0]).hexdigest() != digest:
                        changed.append(name)
                except WorkspaceError:
                    changed.append(name)
            roots = record["request"]["source"]["roots"]
            for name in workspace.list():
                if (
                    name.endswith(".py")
                    and name not in expected
                    and any(
                        PurePosixPath(name).is_relative_to(PurePosixPath(root)) for root in roots
                    )
                ):
                    changed.append(name)
            return {"runId": run_id, "matches": not changed, "changed": sorted(changed)}

        @app.get("/api/v1/profiles")
        def profiles():
            return {"items": configuration.list("profiles")}

        @app.put("/api/v1/profiles/{name}")
        def save_profile(name: str, payload: DataProfile):
            return configuration.put("profiles", name, payload.model_dump())

        @app.get("/api/v1/presets")
        def presets():
            return {"items": configuration.list("presets")}

        @app.put("/api/v1/presets/{name}")
        def save_preset(name: str, payload: Preset):
            return configuration.put("presets", name, payload.model_dump())

        @app.get("/api/v1/files")
        def list_files():
            return {"files": workspace.list()}

        @app.get("/api/v1/file")
        def read_file(path: str):
            return workspace.read(path)

        @app.put("/api/v1/file")
        def save_file(payload: FileWrite):
            return workspace.save(payload.path, payload.baseRevision, payload.content)

        @app.post("/api/v1/discover")
        async def describe(payload: SourceRequest):
            if not environment["compatible"]:
                raise WorkspaceError("InterpreterIncompatible", environment["message"], 422)
            snapshot = await run_in_threadpool(workspace.capture, payload)
            return await run_in_threadpool(discover, python, snapshot, timeout=discover_timeout)

        @app.post("/api/v1/runs")
        async def submit(payload: RunRequest):
            return await run_in_threadpool(manager().submit, payload)

        @app.post("/api/v1/runs/{run_id}/rerun")
        async def rerun(run_id: str):
            return await run_in_threadpool(manager().rerun, run_id)

        @app.post("/api/v1/runs/{run_id}/cancel")
        def cancel(run_id: str):
            return manager().cancel(run_id)

        @app.get("/api/v1/events")
        async def events(request: Request, after: int = 0, instance: str | None = None):
            host = manager()

            async def stream():
                cursor = after
                while not await request.is_disconnected():
                    if host is not app.state.manager:
                        yield 'event: reset\ndata: {"workspaceChanged": true}\n\n'
                        return
                    batch = host.events_after(cursor, instance)
                    if batch["expired"]:
                        yield "event: reset\ndata: " + json.dumps(batch) + "\n\n"
                        return
                    for event in batch["events"]:
                        cursor = event["sequence"]
                        yield f"id: {cursor}\ndata: " + json.dumps(event) + "\n\n"
                    yield ": keepalive\n\n"
                    await asyncio.sleep(1)

            return StreamingResponse(stream(), media_type="text/event-stream")

        @app.post("/api/v1/imports")
        async def import_result(request: Request):
            import shutil

            run_id = uuid.uuid4().hex
            host = manager()
            directory = host.runs / run_id
            directory.mkdir()
            temporary = directory / "upload"
            try:
                size = 0
                with temporary.open("wb") as file:
                    async for chunk in request.stream():
                        size += len(chunk)
                        if size > 512 * 1024 * 1024:
                            raise WorkspaceError(
                                "ImportTooLarge", "Import exceeds the size limit", 413
                            )
                        file.write(chunk)
                if request.headers.get("content-type") == "application/json":
                    manifest = await run_in_threadpool(
                        import_portfolio, temporary, directory / "result"
                    )
                else:
                    manifest = await run_in_threadpool(
                        import_container, temporary, directory / "result"
                    )
                record = {
                    "id": run_id,
                    "status": "succeeded",
                    "imported": True,
                    "idempotencyKey": "import-" + run_id,
                    "requestHash": run_id,
                    "sourceRunId": manifest.runId,
                    "provenance": manifest.provenance,
                }
                host._save(record)
                return record
            except Exception as failure:
                from zipfile import BadZipFile

                from jsonschema.exceptions import ValidationError

                if not isinstance(
                    failure,
                    (ValueError, TypeError, KeyError, ValidationError, BadZipFile, WorkspaceError),
                ):
                    shutil.rmtree(directory)
                    raise
                if isinstance(failure, WorkspaceError):
                    shutil.rmtree(directory)
                    raise
                shutil.rmtree(directory)
                if isinstance(failure, ValidationError):
                    message = f"Invalid report at {failure.json_path}: {failure.message}"
                elif isinstance(failure, KeyError):
                    message = f"Missing artifact field: {failure.args[0]}"
                else:
                    message = str(failure)
                raise WorkspaceError("InvalidArtifact", message[:800], 422) from failure
            finally:
                temporary.unlink(missing_ok=True)

    static = Path(str(files("openbacktesting_studio").joinpath("web")))
    if static.is_dir():
        app.mount("/", StaticFiles(directory=static, html=True), name="web")
    return app
