import json
import sys
import time

import pytest

from openbacktesting_studio.execution.manager import RunManager
from openbacktesting_studio.execution.process import discover, probe
from openbacktesting_studio.protocol import RunRequest, SourceRequest
from openbacktesting_studio.workspace import Workspace, WorkspaceError

SOURCE = """from openbacktesting import Strategy, backtest
@backtest()
class Example(Strategy):
    def init(self): pass
    def next(self):
        if self.bar_index == 0: self.buy(qty=1)
"""


def request(workspace, text=SOURCE, key="one"):
    (workspace.root / "strategy.py").write_text(text)
    source = SourceRequest(path="strategy.py", revision=workspace.read("strategy.py")["revision"])
    description = discover(sys.executable, workspace.capture(source))["description"]
    return RunRequest(
        source=source,
        inputs={key: description[key] for key in ["schemaVersion", "schemaHash"]} | {"values": {}},
        data={
            "name": "GOOG",
            "kind": "sample",
            "sample": "GOOG",
            "timezone": "UTC",
            "timeframe": {"unit": "day", "multiplier": 1},
            "instrument": {"symbol": "GOOG"},
        },
        idempotencyKey=key,
    )


def wait(manager, run_id, target=None):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        record = manager.get(run_id)
        if record["status"] == target or record["status"] in {"succeeded", "failed", "cancelled"}:
            return record
        time.sleep(0.02)
    pytest.fail("Run did not reach the expected state")


def test_real_run_idempotency_and_durable_result(tmp_path):
    workspace = Workspace(tmp_path)
    manager = RunManager(workspace, sys.executable, probe(sys.executable))
    try:
        payload = request(workspace)
        queued = manager.submit(payload)
        assert manager.submit(payload)["id"] == queued["id"]
        with pytest.raises(WorkspaceError, match="different request"):
            manager.submit(payload.model_copy(update={"settings": {"cash": 20000}}))
        final = wait(manager, queued["id"])
        assert final["status"] == "succeeded", final
        result = manager.result_path(queued["id"])
        assert (result / "portfolio.json").is_file() and (result / "plotting.json").is_file()
        assert (
            json.loads((result / "manifest.json").read_text())["provenance"]["dataHash"]
            == final["dataHash"]
        )
        assert manager.cancel(queued["id"])["status"] == "succeeded"
    finally:
        manager.close()
    reopened = RunManager(workspace, sys.executable, probe(sys.executable))
    try:
        assert reopened.get(queued["id"])["status"] == "succeeded"
    finally:
        reopened.close()


def test_running_cancel_reclaims_hung_strategy(tmp_path):
    workspace = Workspace(tmp_path)
    manager = RunManager(workspace, sys.executable, probe(sys.executable))
    try:
        payload = request(
            workspace,
            SOURCE.replace("def init(self): pass", "def init(self):\n        while True: pass"),
        )
        queued = manager.submit(payload)
        assert wait(manager, queued["id"], "running")["status"] == "running"
        manager.cancel(queued["id"])
        assert wait(manager, queued["id"])["status"] == "cancelled"
    finally:
        manager.close()


def test_bounded_queue_cancelled_loader_never_runs_and_events_reset(tmp_path):
    workspace = Workspace(tmp_path)
    manager = RunManager(workspace, sys.executable, probe(sys.executable), queue_limit=1)
    try:
        first = manager.submit(
            request(
                workspace,
                SOURCE.replace("def init(self): pass", "def init(self):\n        while True: pass"),
            )
        )
        wait(manager, first["id"], "running")
        second_request = request(workspace, key="second")
        (tmp_path / "loader.py").write_text(
            'def load_data():\n    raise RuntimeError("LOADER_MUST_NOT_EXECUTE")\n'
        )
        second_request.data = second_request.data.model_copy(
            update={"kind": "loader", "sample": None, "path": "loader.py", "function": "load_data"}
        )
        second = manager.submit(second_request)
        assert second["status"] == "queued"
        with pytest.raises(WorkspaceError) as failure:
            manager.submit(second_request.model_copy(update={"idempotencyKey": "third"}))
        assert failure.value.code == "QueueFull"
        assert manager.cancel(second["id"])["status"] == "cancelled"
        assert not (manager.runs / second["id"] / "response.json").exists()
        events = manager.events_after(0)
        assert [event["sequence"] for event in events["events"]] == sorted(
            event["sequence"] for event in events["events"]
        )
        assert manager.events_after(events["sequence"])["events"] == []
        assert manager.events_after(0, "old-instance")["expired"]
        manager.cancel(first["id"])
        assert wait(manager, first["id"])["status"] == "cancelled"
    finally:
        manager.close()


def test_worker_state_is_fresh_and_exports_share_one_random_execution(tmp_path):
    workspace = Workspace(tmp_path)
    manager = RunManager(workspace, sys.executable, probe(sys.executable))
    source = (
        SOURCE.replace("from openbacktesting", "import random\nCOUNTER = 0\nfrom openbacktesting")
        .replace(
            "def init(self): pass",
            "def init(self):\n        global COUNTER\n        COUNTER += 1\n        assert COUNTER == 1\n        self.quantity = random.randint(1, 20)",
        )
        .replace("self.buy(qty=1)", "self.buy(qty=self.quantity)")
    )
    try:
        parent = None
        for key in ["first", "second"]:
            payload = request(workspace, source, key)
            payload.parentRunId = parent
            record = manager.submit(payload)
            final = wait(manager, record["id"])
            assert final["status"] == "succeeded", final
            directory = manager.result_path(record["id"])
            portfolio = json.loads((directory / "portfolio.json").read_text())
            plotting = json.loads((directory / "plotting.json").read_text())
            assert [
                {
                    key: row[key]
                    for key in [
                        "fill_id",
                        "order_id",
                        "bar_index",
                        "phase",
                        "sequence",
                        "side",
                        "qty",
                        "price",
                        "fee",
                    ]
                }
                for row in portfolio["facts"]["fills"]
            ] == plotting["tradingFacts"]["fills"]
            assert final["parentRunId"] == parent
            parent = record["id"]
    finally:
        manager.close()


def test_invalid_inputs_fail_before_init_and_map_title(tmp_path):
    workspace = Workspace(tmp_path)
    manager = RunManager(workspace, sys.executable, probe(sys.executable))
    source = (
        SOURCE.replace("Strategy, backtest", "Strategy, backtest, inputs")
        .replace(
            "class Example(Strategy):",
            'class Example(Strategy):\n    n = inputs.int(2, title="Length", minval=1)',
        )
        .replace(
            "def init(self): pass",
            'def init(self):\n        raise RuntimeError("INIT_MUST_NOT_RUN")',
        )
    )
    try:
        payload = request(workspace, source)
        payload.inputs.values = {"Length": False}
        final = wait(manager, manager.submit(payload)["id"])
        assert final["status"] == "failed"
        assert final["error"]["code"] == "InvalidInputValue"
        assert "Length" in final["error"]["fieldErrors"]
        assert "INIT_MUST_NOT_RUN" not in final["error"]["message"]
    finally:
        manager.close()


def test_restart_marks_unfinished_and_isolates_corruption(tmp_path):
    workspace = Workspace(tmp_path)
    manager = RunManager(workspace, sys.executable, probe(sys.executable))
    try:
        complete = manager.submit(request(workspace))
        assert wait(manager, complete["id"])["status"] == "succeeded"
        directory = manager.result_path(complete["id"])
        (directory / "portfolio.json").write_text("{}")
        manager._save(
            {
                "id": "interrupted",
                "status": "running",
                "idempotencyKey": "old",
                "requestHash": "old",
            }
        )
    finally:
        manager.close()
    recovered = RunManager(workspace, sys.executable, probe(sys.executable))
    try:
        assert recovered.get("interrupted")["error"]["code"] == "host_restarted"
        assert recovered.get(complete["id"])["error"]["code"] == "ArtifactCorrupt"
        assert recovered.active is None and not recovered.queue
    finally:
        recovered.close()


def test_persistence_failure_is_not_success(tmp_path, monkeypatch):
    workspace = Workspace(tmp_path)
    manager = RunManager(workspace, sys.executable, probe(sys.executable))

    def fail(*args, **kwargs):
        raise OSError("disk failure")

    monkeypatch.setattr("openbacktesting_studio.execution.manager.write_manifest", fail)
    try:
        final = wait(manager, manager.submit(request(workspace))["id"])
        assert final["status"] == "failed"
        assert "disk failure" in final["error"]["message"]
        with pytest.raises(WorkspaceError):
            manager.result_path(final["id"])
    finally:
        manager.close()


def test_queued_csv_is_frozen_and_rerun_uses_saved_data_and_source(tmp_path):
    workspace = Workspace(tmp_path)
    manager = RunManager(workspace, sys.executable, probe(sys.executable))
    try:
        blocker = manager.submit(
            request(
                workspace,
                SOURCE.replace("def init(self): pass", "def init(self):\n        while True: pass"),
            )
        )
        wait(manager, blocker["id"], "running")
        payload = request(workspace, key="csv")
        (tmp_path / "prices.csv").write_text(
            "Date,Open,High,Low,Close\n2026-01-01,10,11,9,10\n2026-01-02,12,13,11,12\n2026-01-03,14,15,13,14\n"
        )
        payload.data = payload.data.model_copy(
            update={
                "kind": "csv",
                "sample": None,
                "path": "prices.csv",
                "timeColumn": "Date",
                "sourceTimezone": "UTC",
            }
        )
        queued = manager.submit(payload)
        (tmp_path / "prices.csv").write_text("invalid after queue")
        (tmp_path / "strategy.py").write_text("invalid after queue")
        manager.cancel(blocker["id"])
        wait(manager, blocker["id"])
        final = wait(manager, queued["id"])
        assert final["status"] == "succeeded", final
        directory = manager.result_path(queued["id"])
        before = (directory / "portfolio.json").read_bytes()
        fills = json.loads(before)["facts"]["fills"]
        assert fills[0]["price"] == 12
        rerun = manager.rerun(queued["id"])
        repeated = wait(manager, rerun["id"])
        assert repeated["status"] == "succeeded", repeated
        assert repeated["parentRunId"] == queued["id"]
        assert repeated["dataHash"] == final["dataHash"]
        assert (directory / "portfolio.json").read_bytes() == before
        assert not list((directory / "source").rglob("*.pyc"))
    finally:
        manager.close()


def test_loader_parameters_resources_and_exceptions_execute_in_worker(tmp_path):
    workspace = Workspace(tmp_path)
    manager = RunManager(workspace, sys.executable, probe(sys.executable))
    try:
        payload = request(workspace)
        (tmp_path / "loader.py").write_text(
            'import pandas as pd\ndef load_data(size):\n    price = float(open("price.txt").read())\n    return pd.DataFrame({key: [price] * size for key in ["Open", "High", "Low", "Close"]}, index=pd.date_range("2026-01-01", periods=size, tz="UTC"))\n'
        )
        (tmp_path / "price.txt").write_text("20")
        payload.data = payload.data.model_copy(
            update={
                "kind": "loader",
                "sample": None,
                "path": "loader.py",
                "function": "load_data",
                "parameters": {"size": 3},
                "resources": ["price.txt"],
            }
        )
        final = wait(manager, manager.submit(payload)["id"])
        assert final["status"] == "succeeded", final
        changed = payload.model_copy(update={"idempotencyKey": "loader-fails"})
        changed.data = payload.data.model_copy(update={"parameters": {"bad_parameter": True}})
        failed = wait(manager, manager.submit(changed)["id"])
        assert failed["status"] == "failed"
        assert failed["error"]["phase"] == "loading"
    finally:
        manager.close()


def test_temporary_termination_failure_retains_active_slot(tmp_path, monkeypatch):
    from openbacktesting_studio.execution.process import ManagedProcess

    workspace = Workspace(tmp_path)
    manager = RunManager(workspace, sys.executable, probe(sys.executable))
    original = ManagedProcess.terminate
    attempts = []

    def terminate(process, grace=3):
        if process is manager.process and not attempts:
            attempts.append("denied")
            raise PermissionError("temporary termination denial")
        return original(process, grace)

    monkeypatch.setattr(ManagedProcess, "terminate", terminate)
    try:
        run = manager.submit(
            request(
                workspace,
                SOURCE.replace("def init(self): pass", "def init(self):\n        while True: pass"),
            )
        )
        wait(manager, run["id"], "running")
        manager.cancel(run["id"])
        assert wait(manager, run["id"])["status"] == "cancelled"
        assert attempts == ["denied"]
    finally:
        manager.close()
