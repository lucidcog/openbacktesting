"""One active worker per workspace, durable terminal states, and bounded replay events."""

from __future__ import annotations

import json
import shutil
import sqlite3
import threading
import time
import uuid
from collections import deque
from hashlib import sha256

from openbacktesting_studio.artifacts import strict_json, validate, write_manifest
from openbacktesting_studio.execution.process import ManagedProcess, discover
from openbacktesting_studio.workspace import WorkspaceError

TERMINAL = {"succeeded", "failed", "cancelled"}


class RunManager:
    def __init__(self, workspace, python, environment, *, queue_limit=8):
        self.workspace, self.python, self.environment = workspace, python, environment
        self.root = workspace.root / ".openbacktesting/studio"
        for parent in [self.root.parent, self.root]:
            if parent.is_symlink():
                raise WorkspaceError("PathDenied", "State directory cannot be a link", 403)
            parent.mkdir(exist_ok=True)
        self.runs = self.root / "runs"
        if self.runs.is_symlink():
            raise WorkspaceError("PathDenied", "Runs directory cannot be a link", 403)
        self.runs.mkdir(exist_ok=True)
        if (self.root / "index.sqlite").is_symlink():
            raise WorkspaceError("PathDenied", "Run index cannot be a link", 403)
        import fcntl

        lock_path = self.root / "workspace.lock"
        if lock_path.is_symlink():
            raise WorkspaceError("PathDenied", "Host lock cannot be a link", 403)
        self.host_lock = lock_path.open("a")
        try:
            fcntl.flock(self.host_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as failure:
            self.host_lock.close()
            raise WorkspaceError(
                "WorkspaceBusy", "Another Studio host owns this workspace", 409
            ) from failure
        self.database = sqlite3.connect(self.root / "index.sqlite", check_same_thread=False)
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, idem TEXT UNIQUE, digest TEXT, record TEXT)"
        )
        self.lock = threading.Condition(threading.RLock())
        self.queue_limit = queue_limit
        self.events = deque(maxlen=1000)
        self.sequence = 0
        self.instance = uuid.uuid4().hex
        self.queue = deque()
        self.active = None
        self.process = None
        self.stopping = False
        for record in self.history():
            if record["status"] not in TERMINAL:
                record.update(
                    status="failed",
                    error={
                        "code": "host_restarted",
                        "message": "The previous host stopped before completion",
                    },
                )
                self._save(record)
            elif record["status"] == "succeeded":
                try:
                    validate(self.runs / record["id"] / "result")
                except (OSError, ValueError) as error:
                    record.update(
                        status="failed", error={"code": "ArtifactCorrupt", "message": str(error)}
                    )
                    self._save(record)
        from openbacktesting_studio.execution.optimization import OptimizationManager

        self.optimizer = OptimizationManager(self)
        self.thread = threading.Thread(target=self._work, daemon=True)
        self.thread.start()

    def _save(self, record):
        with self.lock:
            self.database.execute(
                "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?)",
                (
                    record["id"],
                    record["idempotencyKey"],
                    record["requestHash"],
                    json.dumps(record, allow_nan=False),
                ),
            )
            self.database.commit()
            self.sequence += 1
            self.events.append(
                {
                    "sequence": self.sequence,
                    "instance": self.instance,
                    "type": "run",
                    "run": {
                        key: record[key]
                        for key in ["id", "status", "phase", "startedAt", "finishedAt"]
                        if key in record
                    },
                }
            )
            self.lock.notify_all()

    def history(self):
        with self.lock:
            return [
                json.loads(row[0])
                for row in self.database.execute("SELECT record FROM runs ORDER BY rowid DESC")
            ]

    def get(self, run_id):
        with self.lock:
            row = self.database.execute("SELECT record FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise WorkspaceError("RunNotFound", "Run does not exist", 404)
            return json.loads(row[0])

    def events_after(self, after, instance=None):
        with self.lock:
            expired = (
                after < 0
                or after > self.sequence
                or instance not in {None, self.instance}
                or (self.events and after < self.events[0]["sequence"] - 1)
            )
            return {
                "instance": self.instance,
                "expired": bool(expired),
                "sequence": self.sequence,
                "events": []
                if expired
                else [event for event in self.events if event["sequence"] > after],
            }

    def submit(self, request, *, frozen_snapshot=None, frozen_data=None):
        payload = request.model_dump()
        digest = sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()
        with self.lock:
            if self.optimizer.active:
                raise WorkspaceError(
                    "WorkspaceBusy", "Finish or cancel the active experiment first", 409
                )
            row = self.database.execute(
                "SELECT record FROM runs WHERE idem=?", (request.idempotencyKey,)
            ).fetchone()
            if row:
                record = json.loads(row[0])
                if record["requestHash"] != digest:
                    raise WorkspaceError(
                        "IdempotencyConflict",
                        "This key already identifies a different request",
                        409,
                    )
                return record
            if request.parentRunId is not None:
                self.get(request.parentRunId)
            if self.stopping:
                raise WorkspaceError("HostStopping", "The host is stopping", 409)
            if len(self.queue) >= self.queue_limit:
                raise WorkspaceError("QueueFull", "The local run queue is full", 429)
        extra = list(request.data.resources)
        if request.data.path:
            extra.append(request.data.path)
        snapshot = frozen_snapshot or self.workspace.capture(request.source, extra)
        # Discovery runs in another interpreter; it never starts strategy lifecycle or loader.
        description = discover(self.python, snapshot)
        schema = description["description"]
        if (
            request.inputs.schemaHash != schema["schemaHash"]
            or request.inputs.schemaVersion != schema["schemaVersion"]
        ):
            raise WorkspaceError("SchemaOutdated", "Rediscover inputs for this source version", 409)
        run_id = uuid.uuid4().hex
        record = {
            "id": run_id,
            "status": "queued",
            "phase": None,
            "createdAt": time.time(),
            "idempotencyKey": request.idempotencyKey,
            "requestHash": digest,
            "sourceHash": snapshot["hash"],
            "parentRunId": request.parentRunId,
            "sourceFiles": snapshot["files"],
            "request": payload,
            "environment": self.environment,
        }
        with self.lock:
            # A second concurrent submission may have won during discovery.
            row = self.database.execute(
                "SELECT record FROM runs WHERE idem=?", (request.idempotencyKey,)
            ).fetchone()
            if row:
                other = json.loads(row[0])
                if other["requestHash"] != digest:
                    raise WorkspaceError("IdempotencyConflict", "Key used by another request", 409)
                return other
            if self.optimizer.active:
                raise WorkspaceError("WorkspaceBusy", "An experiment started during discovery", 409)
            if self.stopping or len(self.queue) >= self.queue_limit:
                raise WorkspaceError("QueueFull", "The local run queue is unavailable", 429)
            directory = self.runs / run_id
            directory.mkdir()
            (directory / "worker-request.json").write_text(
                json.dumps(
                    {
                        "operation": "run",
                        "dataSnapshot": str(frozen_data) if frozen_data else None,
                        "snapshot": snapshot,
                        "request": payload,
                    }
                )
            )
            self._save(record)
            self.queue.append(run_id)
            self.lock.notify_all()
        return record

    def cancel(self, run_id):
        with self.lock:
            record = self.get(run_id)
            if record["status"] in TERMINAL:
                return record
            if record["status"] == "queued":
                self.queue.remove(run_id)
                record["status"] = "cancelled"
            else:
                record["status"] = "cancelling"
            self._save(record)
            return record

    def _work(self):
        while True:
            with self.lock:
                self.lock.wait_for(lambda: self.queue or self.stopping)
                if self.stopping:
                    return
                run_id = self.queue.popleft()
                self.active = run_id
                record = self.get(run_id)
                record.update(status="running", phase="loading", startedAt=time.time())
                self._save(record)
            directory = self.runs / run_id
            response = directory / "response.json"
            try:
                process = ManagedProcess(
                    [
                        self.python,
                        "-m",
                        "openbacktesting_studio.execution.worker",
                        str(directory / "worker-request.json"),
                        str(response),
                    ]
                )
                with self.lock:
                    self.process = process
                while process.process.poll() is None:
                    with self.lock:
                        cancelling = self.get(run_id)["status"] == "cancelling"
                    if cancelling:
                        process.terminate()
                        break
                    phase_file = directory / "phase.json"
                    if phase_file.exists():
                        stage = strict_json(phase_file.read_bytes())["phase"]
                        with self.lock:
                            record = self.get(run_id)
                            if record["phase"] != stage and record["status"] == "running":
                                record["phase"] = stage
                                self._save(record)
                    time.sleep(0.05)
                exit_code = process.wait()
                result = (
                    strict_json(response.read_bytes())
                    if response.exists()
                    else {"ok": False, "message": "Worker exited without a response"}
                )
                with self.lock:
                    record = self.get(run_id)
                    record.update(
                        finishedAt=time.time(),
                        stdout=process.stdout.export(),
                        stderr=process.stderr.export(),
                    )
                    if record["status"] == "cancelling":
                        record.update(status="cancelled", logsIncomplete=True)
                    elif exit_code or not result.get("ok"):
                        record.update(status="failed", error=result)
                    else:
                        output = directory / "artifacts"
                        original = strict_json((directory / "worker-request.json").read_bytes())
                        shutil.copytree(
                            original["snapshot"]["directory"],
                            output / "source",
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                        )
                        for name, value in [
                            ("stdout", record["stdout"]),
                            ("stderr", record["stderr"]),
                        ]:
                            (output / f"{name}.json").write_text(json.dumps(value))
                        provenance = {
                            "sourceHash": record["sourceHash"],
                            "dataHash": result["dataHash"],
                            "requestHash": record["requestHash"],
                            "environment": record["environment"],
                            "parentRunId": record["parentRunId"],
                            "externalDependencies": "Not captured; declared resources only",
                        }
                        write_manifest(
                            output,
                            run_id=run_id,
                            provenance=provenance,
                            diagnostics=result["diagnostics"],
                        )
                        validate(output)
                        output.replace(directory / "result")
                        record.update(
                            status="succeeded",
                            dataHash=result["dataHash"],
                            diagnostics=result["diagnostics"],
                        )
                    self._save(record)
            except BaseException as failure:  # noqa: BLE001 - preserve failed job state at worker boundary
                with self.lock:
                    record = self.get(run_id)
                    # Failed process termination is not falsely reported as cancellation.
                    alive = self.process is not None and self.process.process.poll() is None
                    status = (
                        "cancelling" if record["status"] == "cancelling" and alive else "failed"
                    )
                    record.update(
                        status=status,
                        error={"code": type(failure).__name__, "message": str(failure)},
                    )
                    self._save(record)
            finally:
                # Retain the active slot until the process has actually stopped.
                # A denied termination must never let the queue launch a second worker.
                while self.process is not None and self.process.process.poll() is None:
                    try:
                        self.process.terminate()
                    except (OSError, TimeoutError):
                        time.sleep(1)
                with self.lock:
                    final = self.get(run_id)
                    if final["status"] == "cancelling":
                        final.update(
                            status="cancelled", logsIncomplete=True, finishedAt=time.time()
                        )
                        self._save(final)
                    self.active, self.process = None, None

    def rerun(self, run_id):
        from openbacktesting_studio.protocol import RunRequest

        directory = self.result_path(run_id)
        manifest = validate(directory)
        if (
            not (directory / "source").is_dir()
            or not (directory / "data/schema.json").is_file()
            or not (directory / "request.json").is_file()
        ):
            raise WorkspaceError(
                "RerunUnavailable",
                "Source, normalized data and request snapshots are required",
                409,
            )
        original = self.get(run_id)
        if original.get("imported"):
            raise WorkspaceError(
                "RerunUnavailable",
                "Imported source is not executed by the viewer; create a trusted workspace first",
                409,
            )
        if manifest.provenance.get("environment") != self.environment:
            raise WorkspaceError(
                "EnvironmentChanged",
                "The selected interpreter differs from the saved run; configure an explicit new run",
                409,
            )
        request = RunRequest.model_validate(strict_json((directory / "request.json").read_bytes()))
        request.idempotencyKey = uuid.uuid4().hex
        request.parentRunId = run_id
        target = self.root / "snapshots" / ("rerun-" + uuid.uuid4().hex)
        shutil.copytree(directory / "source", target)
        snapshot = {
            "directory": str(target),
            "entry": request.source.path,
            "roots": request.source.roots,
            "files": original["sourceFiles"],
            "hash": original["sourceHash"],
        }
        return self.submit(request, frozen_snapshot=snapshot, frozen_data=directory / "data")

    def result_path(self, run_id):
        record = self.get(run_id)
        if record["status"] != "succeeded":
            raise WorkspaceError("ResultUnavailable", "This run has no completed result", 409)
        path = self.runs / run_id / "result"
        try:
            validate(path)
        except (ValueError, OSError) as error:
            raise WorkspaceError("ArtifactCorrupt", str(error), 422) from error
        return path

    def close(self):
        with self.lock:
            self.stopping = True
            for run_id in list(self.queue):
                self.cancel(run_id)
            if self.active:
                self.cancel(self.active)
            self.lock.notify_all()
        self.optimizer.close()
        self.thread.join(timeout=15)
        if self.thread.is_alive():
            raise RuntimeError("Worker shutdown has not completed")
        self.database.close()
        self.host_lock.close()
