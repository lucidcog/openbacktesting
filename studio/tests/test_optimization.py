"""Real worker/API coverage for Studio's complete core optimizer workflow."""

import json
import time

import pytest
from test_host import ORIGIN, TOKEN, session

from openbacktesting_studio.host import create_app

SOURCE = """from pathlib import Path
from openbacktesting import Strategy, backtest, inputs
@backtest()
class SearchStrategy(Strategy):
    length = inputs.int(1, title="Length")
    flag = inputs.bool(True, title="Flag")
    def init(self):
        Path("executed").touch()
    def next(self):
        if self.bar_index == 1: self.buy(qty=self.length)
def acceptable(values):
    return values["Length"] != 2
"""


def payload(client, tmp_path, source=SOURCE):
    (tmp_path / "search.py").write_text(source)
    file = client.get("/api/v1/file", params={"path": "search.py"}).json()
    saved = {"path": "search.py", "revision": file["revision"]}
    description = client.post("/api/v1/discover", json=saved).json()["description"]
    return {
        "run": {
            "source": saved,
            "inputs": {
                "schemaVersion": description["schemaVersion"],
                "schemaHash": description["schemaHash"],
                "values": {},
            },
            "settings": {},
            "idempotencyKey": "plan-test",
            "data": {
                "name": "short",
                "kind": "sample",
                "sample": "GOOG",
                "timezone": "UTC",
                "end": "2004-08-31T00:00:00Z",
                "timeframe": {"unit": "day", "multiplier": 1},
                "instrument": {"symbol": "GOOG"},
            },
        },
        "search": {
            "Length": {"kind": "range", "start": 1, "stop": 3, "step": 1},
            "Flag": {"kind": "values", "values": [True, False]},
        },
        "constraint": "acceptable",
    }


def wait(client, identifier):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/optimizations/{identifier}")
        assert response.status_code == 200, response.text
        row = response.json()
        if row["status"] not in {"planning", "running", "cancelling"}:
            return row
        time.sleep(0.03)
    pytest.fail("Optimizer did not finish")


def test_plan_execute_query_trial_backup_import_and_reopen(tmp_path):
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        response = client.post("/api/v1/optimizations", json=payload(client, tmp_path))
        assert response.status_code == 200, response.text
        identifier = response.json()["id"]
        prefix = f"/api/v1/optimizations/{identifier}"
        planned = wait(client, identifier)
        assert planned["status"] == "planned", planned
        assert planned["plan"]["total"] == 6
        assert not list(tmp_path.glob(".openbacktesting/studio/snapshots/**/executed"))
        assert client.post(prefix + "/start").status_code == 200
        completed = wait(client, identifier)
        assert completed["status"] == "completed", completed
        assert completed["info"]["committed"] == 4
        assert completed["info"]["skipped"] == 2
        fields = client.get(prefix + "/fields").json()["fields"]
        assert any(field["path"] == "summary.all.totalPnl.value" for field in fields)
        query = {
            "fields": ["summary.all.totalPnl.value"],
            "order_by": [["summary.all.totalPnl.value", "desc"]],
            "filters": [["summary.all.totalPnl.value", "status", "ok"]],
            "limit": 2,
        }
        page = client.post(prefix + "/query", json=query)
        assert page.status_code == 200, page.text
        page = page.json()
        assert len(page["rows"]) == 2 and page["cursor"]
        next_page = client.post(prefix + "/query", json=query | {"cursor": page["cursor"]}).json()
        assert not {row["trial_id"] for row in page["rows"]} & {
            row["trial_id"] for row in next_page["rows"]
        }
        trial = page["rows"][0]["trial_id"]
        portfolio = client.get(prefix + f"/trials/{trial}/portfolio").json()
        opened = client.post(prefix + f"/trials/{trial}/open").json()
        assert (
            client.get(f"/api/v1/runs/{opened['id']}/summary").json()["summary"]
            == portfolio["summary"]
        )
        assert client.post(prefix + f"/trials/{trial}/open").json()["id"] == opened["id"]
        rows = client.get(prefix + "/trials").json()["rows"]
        assert len(rows) == 6 and sum(row["state"] == "skipped_constraint" for row in rows) == 2
        backup = client.get(prefix + "/export")
        assert backup.status_code == 200 and backup.content.startswith(b"SQLite format 3")
        restored = client.post("/api/v1/optimizations/import", content=backup.content).json()
        assert restored["imported"] and restored["info"]["committed"] == 4
        assert client.post(f"/api/v1/optimizations/{restored['id']}/start").status_code == 409
        assert client.post(prefix + "/query", json={"fields": ["not.a.field"]}).status_code == 422
        assert client.get(prefix + "/trials?offset=-1").status_code == 422
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        assert client.get(prefix).json()["info"]["committed"] == 4
        assert len(client.get("/api/v1/optimizations").json()["items"]) == 2


def test_cancel_resume_frozen_source_and_exclusive_workspace(tmp_path):
    slow = SOURCE.replace('Path("executed").touch()', "import time; time.sleep(0.15)")
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        request = payload(client, tmp_path, slow)
        request["search"]["Length"]["stop"] = 10
        identifier = client.post("/api/v1/optimizations", json=request).json()["id"]
        prefix = f"/api/v1/optimizations/{identifier}"
        assert wait(client, identifier)["status"] == "planned"
        client.post(prefix + "/start")
        assert client.post("/api/v1/runs", json=request["run"]).status_code == 409
        other = tmp_path / "other"
        other.mkdir()
        assert client.put("/api/v1/workspace", json={"path": str(other)}).status_code == 409
        client.post(prefix + "/cancel")
        assert wait(client, identifier)["status"] == "cancelled"
        (tmp_path / "search.py").write_text('raise RuntimeError("changed disk must not execute")')
        assert client.post(prefix + "/start").status_code == 200
        completed = wait(client, identifier)
        assert completed["status"] == "completed", completed
        assert completed["info"]["committed"] == 18
        assert completed["info"]["skipped"] == 2


def test_invalid_domain_and_constraint_fail_before_execution(tmp_path):
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        request = payload(client, tmp_path)
        request["search"]["Length"]["step"] = 0
        identifier = client.post("/api/v1/optimizations", json=request).json()["id"]
        assert "positive step" in wait(client, identifier)["error"]
        assert not list(tmp_path.glob(".openbacktesting/studio/snapshots/**/executed"))
        assert (
            client.post("/api/v1/optimizations/import", content=b"not a database").status_code
            == 422
        )
        assert client.get("/api/v1/optimizations/bad-id").status_code == 404


def test_all_input_types_and_decimal_ranges_keep_core_plan_and_query_semantics(tmp_path):
    source = """from enum import Enum
from openbacktesting import Strategy, backtest, inputs
class Mode(Enum):
    A = "Alpha"
    B = "Beta"
@backtest()
class Typed(Strategy):
    integer = inputs.int(1, title="Integer")
    decimal = inputs.float(0.1, title="Decimal")
    price = inputs.price(100.0, title="Price")
    flag = inputs.bool(True, title="Flag")
    text = inputs.string("base", title="Text")
    mode = inputs.enum(Mode.A, title="Mode")
    start = inputs.time(0, title="Time")
    session = inputs.session("24x7", title="Session")
    color = inputs.color("#ff0000", title="Color")
    def init(self): pass
    def next(self): pass
"""
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        request = payload(client, tmp_path, source)
        request["constraint"] = None
        request["search"] = {
            title: {"kind": "values", "values": [value]}
            for title, value in {
                "Integer": 2,
                "Flag": False,
                "Text": "comma,text\nsecond line",
                "Mode": "B",
                "Time": 1704067200000,
                "Session": "24x7",
                "Color": "#00ff00",
            }.items()
        }
        request["search"].update(
            {
                "Decimal": {"kind": "range", "start": "0.1", "stop": "0.3", "step": "0.1"},
                "Price": {"kind": "range", "start": "99.5", "stop": "100", "step": "0.5"},
            }
        )
        identifier = client.post("/api/v1/optimizations", json=request).json()["id"]
        prefix = f"/api/v1/optimizations/{identifier}"
        planned = wait(client, identifier)
        assert planned["status"] == "planned", planned
        dimensions = {row["title"]: row["values"] for row in planned["plan"]["dimensions"]}
        assert dimensions["Decimal"] == [0.1, 0.2, 0.3]
        assert dimensions["Session"] == ["0000-0000:1234567"]
        assert len(dimensions) == 9
        assert client.post(prefix + "/start").status_code == 200
        assert wait(client, identifier)["info"]["committed"] == 6
        field = "summary.all.totalPnl.value"
        for operator, value, count in [
            ("eq", 0, 6),
            ("ne", 0, 0),
            ("lt", 1, 6),
            ("le", 0, 6),
            ("gt", 0, 0),
            ("ge", 0, 6),
            ("status", "ok", 6),
        ]:
            response = client.post(
                prefix + "/query",
                json={
                    "fields": [field],
                    "filters": [[field, operator, value]],
                    "order_by": [[field, "asc"], ["summary.all.totalReturn.value", "desc"]],
                },
            )
            assert response.status_code == 200, response.text
            assert len(response.json()["rows"]) == count
        first = client.post(prefix + "/query", json={"fields": [field], "limit": 1}).json()
        assert (
            client.post(
                prefix + "/query", json={"fields": [field], "limit": 2, "cursor": first["cursor"]}
            ).status_code
            == 422
        )
        assert client.post(prefix + "/query", json={"cursor": "broken"}).status_code == 422
        assert client.get(prefix + "/trials?offset=2&limit=2").json()["rows"][0]["ordinal"] == 2


def test_failed_trials_continue_and_restart_does_not_retry_committed_failures(tmp_path):
    from openbacktesting_studio.execution.worker import write_response

    failing = SOURCE.replace(
        'Path("executed").touch()', 'if self.length == 1: raise ValueError("bad candidate")'
    )
    app = create_app(tmp_path, origin=ORIGIN, token=TOKEN)
    with session(app) as client:
        request = payload(client, tmp_path, failing)
        identifier = client.post("/api/v1/optimizations", json=request).json()["id"]
        prefix = f"/api/v1/optimizations/{identifier}"
        assert wait(client, identifier)["status"] == "planned"
        client.post(prefix + "/start")
        completed = wait(client, identifier)
        assert completed["info"]["committed"] == 2 and completed["info"]["failed"] == 2
        failed = [
            row for row in client.get(prefix + "/trials").json()["rows"] if row["state"] == "failed"
        ]
        assert all("bad candidate" in row["error"] and row["attempt"] == 1 for row in failed)
        assert client.get(prefix + f"/trials/{failed[0]['trial_id']}/portfolio").status_code == 422
    record_path = tmp_path / ".openbacktesting/studio/optimizations" / identifier / "record.json"
    record = json.loads(record_path.read_text())
    record["status"] = "running"
    write_response(record_path, record)
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        assert client.get(prefix).json()["status"] == "interrupted"
        assert client.post(prefix + "/start").status_code == 200
        assert wait(client, identifier)["status"] == "completed_with_errors"
        assert all(row["attempt"] == 1 for row in client.get(prefix + "/trials").json()["rows"])


def test_worker_launch_failure_releases_workspace_and_remains_resumable(tmp_path, monkeypatch):
    from threading import Thread

    app = create_app(tmp_path, origin=ORIGIN, token=TOKEN)
    with session(app) as client:
        identifier = client.post("/api/v1/optimizations", json=payload(client, tmp_path)).json()[
            "id"
        ]
        prefix = f"/api/v1/optimizations/{identifier}"
        assert wait(client, identifier)["status"] == "planned"
        with monkeypatch.context() as patch:
            patch.setattr(
                Thread,
                "start",
                lambda self: (_ for _ in ()).throw(ValueError("launch unavailable")),
            )
            assert client.post(prefix + "/start").status_code == 422
        assert client.get(prefix).json()["status"] == "failed"
        assert client.post(prefix + "/start").status_code == 200
        assert wait(client, identifier)["status"] == "completed"


def test_optimizer_routes_require_session_workspace_and_are_absent_in_viewer(tmp_path):
    from fastapi.testclient import TestClient

    app = create_app(tmp_path, origin=ORIGIN, token=TOKEN, choose_workspace=True)
    with TestClient(app, base_url=ORIGIN) as client:
        assert client.get("/api/v1/optimizations").status_code == 403
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN, choose_workspace=True)) as client:
        assert client.get("/api/v1/optimizations").status_code == 409
    with session(create_app(None, origin=ORIGIN, token=TOKEN, readonly=True)) as client:
        assert client.get("/api/v1/optimizations").status_code == 404
        assert client.post("/api/v1/optimizations", json={}).status_code in {404, 405}


def test_real_ema_worker_handles_distribution_metrics_and_full_trade_reports(tmp_path):
    from pathlib import Path

    source = (Path(__file__).resolve().parents[2] / "examples/strategies/ema_inputs.py").read_text()
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        request = payload(client, tmp_path, source)
        request["constraint"] = None
        request["run"]["data"].pop("end")
        request["search"] = {
            "Fast period": {"kind": "values", "values": [12, 13]},
            "Allow shorting": {"kind": "values", "values": [True, False]},
        }
        identifier = client.post("/api/v1/optimizations", json=request).json()["id"]
        prefix = f"/api/v1/optimizations/{identifier}"
        assert wait(client, identifier)["status"] == "planned"
        assert client.post(prefix + "/start").status_code == 200
        completed = wait(client, identifier)
        assert completed["status"] == "completed", completed
        assert completed["info"]["committed"] == 4
        rows = client.post(
            prefix + "/query", json={"fields": ["analysis.distribution.outliers.lower"]}
        ).json()["rows"]
        assert len(rows) == 4
        assert all(
            row["values"]["analysis.distribution.outliers.lower"]["value"] is not None
            for row in rows
        )


def test_forced_cancel_recovers_uncommitted_trial_on_resume(tmp_path):
    hanging = SOURCE.replace(
        'Path("executed").touch()',
        """marker = Path("first-attempt")
        if not marker.exists():
            marker.touch()
            import time
            time.sleep(60)""",
    )
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        request = payload(client, tmp_path, hanging)
        request["search"] = {"Length": {"kind": "values", "values": [1]}}
        request["constraint"] = None
        identifier = client.post("/api/v1/optimizations", json=request).json()["id"]
        prefix = f"/api/v1/optimizations/{identifier}"
        assert wait(client, identifier)["status"] == "planned"
        client.post(prefix + "/start")
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if client.get(prefix).json().get("info", {}).get("running") == 1:
                break
            time.sleep(0.03)
        else:
            pytest.fail("Trial did not start")
        client.post(prefix + "/cancel")
        assert wait(client, identifier)["status"] == "cancelled"
        assert client.post(prefix + "/start").status_code == 200
        assert wait(client, identifier)["info"]["committed"] == 1
        row = client.get(prefix + "/trials").json()["rows"][0]
        assert row["state"] == "succeeded" and row["attempt"] == 2


def test_snapshot_tampering_is_rejected_before_starting_trials(tmp_path):
    from openbacktesting_studio.artifacts import strict_json

    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        request = payload(client, tmp_path)
        identifier = client.post("/api/v1/optimizations", json=request).json()["id"]
        prefix = f"/api/v1/optimizations/{identifier}"
        assert wait(client, identifier)["status"] == "planned"
        saved = strict_json(
            (
                tmp_path / ".openbacktesting/studio/optimizations" / identifier / "request.json"
            ).read_bytes()
        )
        from pathlib import Path

        (Path(saved["snapshot"]["directory"]) / "search.py").write_text(
            'raise RuntimeError("unexpected execution")'
        )
        client.post(prefix + "/start")
        failed = wait(client, identifier)
        assert failed["status"] == "failed" and "Frozen strategy source changed" in failed["error"]
        assert "info" not in failed
