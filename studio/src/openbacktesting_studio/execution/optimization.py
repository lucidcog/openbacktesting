"""Durable Studio experiments wrapping the core optimizer without recomputing its reports."""

import sqlite3
import threading
import time
import uuid

from openbacktesting.optimizer import open_result

from openbacktesting_studio.artifacts import strict_json
from openbacktesting_studio.execution.process import ManagedProcess
from openbacktesting_studio.execution.worker import write_response
from openbacktesting_studio.workspace import WorkspaceError

ACTIVE = {"planning", "running", "cancelling"}


class OptimizationManager:
    def __init__(self, runs):
        self.runs = runs
        self.root = runs.root / "optimizations"
        if self.root.is_symlink():
            raise WorkspaceError("PathDenied", "Optimizer directory cannot be a link", 403)
        self.root.mkdir(exist_ok=True)
        self.active = None
        self.process = None
        self.thread = None
        for path in self.root.glob("*/record.json"):
            record = strict_json(path.read_bytes())
            if record["status"] in ACTIVE:
                record.update(
                    status="interrupted",
                    error="The previous host stopped. Resume uses the saved source and data.",
                )
                write_response(path, record)

    def directory(self, identifier):
        if len(identifier) != 32 or any(ch not in "0123456789abcdef" for ch in identifier):
            raise WorkspaceError("OptimizationNotFound", "Experiment not found", 404)
        path = self.root / identifier
        if path.is_symlink() or not (path / "record.json").is_file():
            raise WorkspaceError("OptimizationNotFound", "Experiment not found", 404)
        return path

    def _save(self, directory, record):
        write_response(directory / "record.json", record)

    def history(self):
        return sorted(
            [strict_json(path.read_bytes()) for path in self.root.glob("*/record.json")],
            key=lambda row: row["createdAt"],
            reverse=True,
        )

    def get(self, identifier):
        path = self.directory(identifier)
        record = strict_json((path / "record.json").read_bytes())
        if (path / "plan.json").exists():
            record["plan"] = strict_json((path / "plan.json").read_bytes())
        if (path / "experiment.sqlite").exists():
            try:
                record["info"] = self.result(identifier).info()
            except (WorkspaceError, sqlite3.Error):
                if record["status"] not in ACTIVE:
                    raise
        return record

    def result(self, identifier):
        path = self.directory(identifier) / "experiment.sqlite"
        if not path.exists():
            raise WorkspaceError("OptimizationPending", "No committed experiment database yet", 409)
        try:
            return open_result(path)
        except (ValueError, OSError) as error:
            raise WorkspaceError("OptimizationInvalid", str(error), 422) from error

    def _reserve(self, identifier):
        if self.runs.stopping or self.active or self.runs.active or self.runs.queue:
            raise WorkspaceError(
                "WorkspaceBusy", "Finish or cancel the active run or experiment first", 409
            )
        self.active = identifier

    def prepare(self, request):
        identifier = uuid.uuid4().hex
        with self.runs.lock:
            self._reserve(identifier)
        try:
            extra = list(request.run.data.resources)
            if request.run.data.path:
                extra.append(request.run.data.path)
            snapshot = self.runs.workspace.capture(request.run.source, extra)
            directory = self.root / identifier
            directory.mkdir()
            record = {
                "id": identifier,
                "createdAt": time.time(),
                "status": "planning",
                "source": request.run.source.path,
                "sourceHash": snapshot["hash"],
                "imported": False,
            }
            self._save(directory, record)
            write_response(
                directory / "request.json", {"request": request.model_dump(), "snapshot": snapshot}
            )
            self._launch(identifier, "plan")
            return record
        except BaseException:
            with self.runs.lock:
                self.active = None
            raise

    def start(self, identifier):
        with self.runs.lock:
            record = self.get(identifier)
            if (
                record.get("imported")
                or record["status"] not in {"planned", "cancelled", "interrupted", "failed"}
                or "plan" not in record
            ):
                raise WorkspaceError(
                    "OptimizationState", "This experiment cannot start or resume", 409
                )
            self._reserve(identifier)
            try:
                self._launch(identifier, "execute")
            except BaseException as error:
                self.active = None
                record.update(status="failed", error=str(error))
                self._save(self.directory(identifier), record)
                raise
        return self.get(identifier)

    def _launch(self, identifier, operation):
        path = self.directory(identifier)
        (path / "cancel").unlink(missing_ok=True)
        (path / "response.json").unlink(missing_ok=True)
        payload = strict_json((path / "request.json").read_bytes()) | {"operation": operation}
        write_response(path / "worker.json", payload)
        record = strict_json((path / "record.json").read_bytes())
        record.update(status="planning" if operation == "plan" else "running", error=None)
        self._save(path, record)
        self.thread = threading.Thread(target=self._work, args=(identifier,), daemon=True)
        self.thread.start()

    def _work(self, identifier):
        path = self.directory(identifier)
        process = None
        outcome = {"status": "failed"}
        try:
            process = ManagedProcess(
                [
                    self.runs.python,
                    "-m",
                    "openbacktesting_studio.execution.optimization_worker",
                    str(path / "worker.json"),
                    str(path / "response.json"),
                ]
            )
            self.process = process
            cancelled_at = None
            while process.process.poll() is None:
                if (path / "cancel").exists():
                    cancelled_at = cancelled_at or time.monotonic()
                    if time.monotonic() - cancelled_at > 3:
                        process.terminate()
                time.sleep(0.05)
            code = process.wait()
            response = (
                strict_json((path / "response.json").read_bytes())
                if (path / "response.json").exists()
                else {"message": "Worker exited without a response"}
            )
            outcome.update(
                status="cancelled"
                if (path / "cancel").exists()
                else response.get("status", "failed")
                if code == 0
                else "failed",
                error=response.get("message"),
                stdout=process.stdout.export(),
                stderr=process.stderr.export(),
            )
        except BaseException as error:  # noqa: BLE001 - preserve worker diagnostics
            outcome.update(error=str(error))
        finally:
            if process and process.process.poll() is None:
                process.terminate()
            # Publish the terminal state and release the workspace in one critical section.
            # A client observing completion can immediately start another operation.
            with self.runs.lock:
                record = strict_json((path / "record.json").read_bytes())
                record.update(outcome)
                self._save(path, record)
                self.active = None
                self.process = None

    def cancel(self, identifier):
        with self.runs.lock:
            path = self.directory(identifier)
            record = strict_json((path / "record.json").read_bytes())
            if record["status"] in ACTIVE:
                (path / "cancel").touch()
                record["status"] = "cancelling"
                self._save(path, record)
            return record

    def import_database(self, data):
        identifier = uuid.uuid4().hex
        path = self.root / identifier
        path.mkdir()
        try:
            database = path / "experiment.sqlite"
            database.write_bytes(data)
            result = open_result(database)
            info = result.info()
            record = {
                "id": identifier,
                "createdAt": time.time(),
                "status": info["status"],
                "source": "Imported experiment",
                "imported": True,
            }
            self._save(path, record)
            write_response(path / "plan.json", info["plan"])
            return self.get(identifier)
        except BaseException:
            import shutil

            shutil.rmtree(path)
            raise

    def close(self):
        if self.active:
            self.cancel(self.active)
        if self.thread:
            self.thread.join(timeout=15)
            if self.thread.is_alive():
                raise RuntimeError("Optimizer worker shutdown has not completed")
