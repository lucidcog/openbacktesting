"""Authenticated workspace-scoped optimizer endpoints using core query semantics."""

import json
import sqlite3
import tempfile
import uuid
from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from openbacktesting_studio.artifacts import import_portfolio
from openbacktesting_studio.protocol import OptimizationQuery, OptimizationRequest
from openbacktesting_studio.workspace import WorkspaceError


def checked(action, *args, **kwargs):
    try:
        return action(*args, **kwargs)
    except (ValueError, TypeError, KeyError, sqlite3.Error) as error:
        raise WorkspaceError("OptimizationInvalid", str(error)[:800], 422) from error


def install_optimizer_routes(app, manager):
    def optimizer():
        return manager().optimizer

    @app.get("/api/v1/optimizations")
    def history():
        return {"items": optimizer().history()}

    @app.post("/api/v1/optimizations")
    async def prepare(payload: OptimizationRequest):
        return await run_in_threadpool(checked, optimizer().prepare, payload)

    @app.post("/api/v1/optimizations/import")
    async def import_database(request: Request):
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > 512 * 1024 * 1024:
                raise WorkspaceError("ImportTooLarge", "Experiment exceeds 512 MiB", 413)
        return await run_in_threadpool(checked, optimizer().import_database, data)

    @app.get("/api/v1/optimizations/{identifier}")
    def detail(identifier: str):
        return checked(optimizer().get, identifier)

    @app.post("/api/v1/optimizations/{identifier}/start")
    def start(identifier: str):
        return checked(optimizer().start, identifier)

    @app.post("/api/v1/optimizations/{identifier}/cancel")
    def cancel(identifier: str):
        return optimizer().cancel(identifier)

    @app.get("/api/v1/optimizations/{identifier}/fields")
    def fields(identifier: str):
        return {"fields": checked(optimizer().result(identifier).fields)}

    @app.post("/api/v1/optimizations/{identifier}/query")
    def query(identifier: str, payload: OptimizationQuery):
        return checked(optimizer().result(identifier).query, **payload.model_dump())

    @app.get("/api/v1/optimizations/{identifier}/trials")
    def trials(identifier: str, offset: int = 0, limit: int = 100):
        result = optimizer().result(identifier)
        return {"rows": checked(result.trials, offset=offset, limit=limit), "info": result.info()}

    @app.get("/api/v1/optimizations/{identifier}/trials/{trial_id}/portfolio")
    def portfolio(identifier: str, trial_id: str):
        return checked(optimizer().result(identifier).load_portfolio, trial_id)

    @app.post("/api/v1/optimizations/{identifier}/trials/{trial_id}/open")
    def open_trial(identifier: str, trial_id: str):
        # Materialize the saved Portfolio for the existing report tabs; never rerun a trial.
        host = manager()
        report = checked(host.optimizer.result(identifier).load_portfolio, trial_id)
        run_id = uuid.uuid5(
            uuid.NAMESPACE_URL, str(host.workspace.root) + identifier + trial_id
        ).hex
        with host.lock:
            if any(row["id"] == run_id for row in host.history()):
                return host.get(run_id)
            directory = host.runs / run_id
            directory.mkdir()
            source = directory / "portfolio-import.json"
            source.write_text(json.dumps(report, allow_nan=False))
            try:
                manifest = import_portfolio(source, directory / "result")
                record = {
                    "id": run_id,
                    "status": "succeeded",
                    "imported": True,
                    "idempotencyKey": "trial-" + run_id,
                    "requestHash": run_id,
                    "sourceRunId": manifest.runId,
                    "optimizationId": identifier,
                    "trialId": trial_id,
                }
                host._save(record)
                return record
            except BaseException:
                import shutil

                shutil.rmtree(directory)
                raise
            finally:
                source.unlink(missing_ok=True)

    @app.get("/api/v1/optimizations/{identifier}/export")
    def export(identifier: str):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "experiment.sqlite"
            checked(optimizer().result(identifier).backup, target)
            # FileResponse must outlive this temporary context.
            import os

            descriptor, output = tempfile.mkstemp(suffix=".sqlite")
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(target.read_bytes())
        return FileResponse(
            output, filename=f"{identifier}.sqlite", background=BackgroundTask(Path(output).unlink)
        )
