"""Real execution, transactions, queries, and boundary regressions for parameter experiments."""

import copy
import json
import sqlite3
from enum import Enum
from pathlib import Path

import pandas as pd
import pytest

from openbacktesting import DataContext, Strategy, Timeframe, backtest, inputs
from openbacktesting.broker import InstrumentSpec
from openbacktesting.data.timeframe import TimeframeUnit
from openbacktesting.optimizer import (
    ExecutionIdentity,
    OptimizationError,
    Range,
    Values,
    open_result,
    plan,
)
from openbacktesting.optimizer.models import encode
from openbacktesting.optimizer.plan import combinations
from openbacktesting.optimizer.runner import execute
from openbacktesting.optimizer.storage import Store, connect, flatten, owner
from openbacktesting.optimizer.validation import validate_report
from openbacktesting.runtime import optimize, resume_optimization, run
from openbacktesting.strategy.inputs import request_for

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ExecutionIdentity("a" * 64, "b" * 64)
CONTEXT = DataContext(Timeframe(TimeframeUnit.DAY, 1), "UTC")


@backtest()
class Scan(Strategy):
    selected = inputs.int(1, title="selected")
    fixed = inputs.int(7, title="fixed")
    threshold = inputs.float(0.1, title="threshold")
    enabled = inputs.bool(True, title="enabled")

    def init(self):
        self.log.info("Do not persist")

    def next(self):
        self.plotting.bg_color("#123456")
        if self.selected == -1:
            raise RuntimeError("Intentional failure")
        if self.enabled and self.bar_index == 0:
            self.buy(qty=self.selected)
        if self.enabled and self.bar_index == 2 and self.selected != 3:
            self.position.close()


def namespace(cls=Scan):
    return {"__name__": cls.__module__, "StrategyType": cls}


def data():
    return pd.DataFrame(
        {k: [100.0, 110.0, 95.0, 108.0] for k in ("Open", "High", "Low", "Close")},
        index=pd.date_range("2026-01-01", periods=4, tz="UTC"),
    )


def kwargs():
    return {
        "identity": IDENTITY,
        "data": data(),
        "context": CONTEXT,
        "instrument": InstrumentSpec(),
        "request": request_for(Scan, {"fixed": 99}),
    }


def launch(tmp_path, **extra):
    return optimize(
        namespace(),
        {"selected": Values([1, 2, 3])},
        path=tmp_path / "results.db",
        **(kwargs() | extra),
    )


def report(request=None):
    from openbacktesting.portfolio import export_result

    return export_result(
        run(
            namespace(),
            request,
            data=data(),
            context=CONTEXT,
            instrument=InstrumentSpec(),
            options={"plotting": False},
        )
    )


def basic_plan(search=None, **options):
    return plan(Scan, search or {"selected": Values([1, 2])}, execution={"version": 1}, **options)


def test_plan_fixed_range_and_freeze():
    request = request_for(Scan, {"fixed": 99})
    p = basic_plan(
        {
            "selected": Range(1, 2, 1),
            "threshold": Range("0.1", "0.3", "0.1"),
            "enabled": Values([False, True]),
        },
        base_inputs=request,
    )
    request["values"]["fixed"] = -7
    rows = list(combinations(p))
    assert p.total == 12 and all(r["values"]["fixed"] == 99 for _, r in rows)
    assert [d["title"] for d in p.snapshot()["dimensions"]] == ["selected", "threshold", "enabled"]
    assert p.snapshot()["dimensions"][1]["values"] == [0.1, 0.2, 0.3]
    assert basic_plan({"threshold": Range(0, 1, "0.3")}).snapshot()["dimensions"][0]["values"] == [
        0.0,
        0.3,
        0.6,
        0.9,
    ]
    assert basic_plan({"selected": Range(1, 1, 1)}).total == 1
    assert all(r["values"]["fixed"] == 7 for _, r in combinations(basic_plan()))


@pytest.mark.parametrize(
    "search",
    [
        {},
        {"unknown": Values([1])},
        {"selected": Values([])},
        {"selected": Values(range(3))},
        {"selected": Values([True])},
        {"selected": Values([1, 1])},
        {"selected": Range(1, 2, 0)},
        {"selected": Range(2, 1, 1)},
        {"selected": Range(1, 2, -1)},
        {"selected": Range("1", "2", "1")},
        {"enabled": Range(0, 1, 1)},
        {"threshold": Values([float("nan")])},
        {"threshold": Values([-0.0, 0.0])},
        {"threshold": Range("oops", "1", "0.1")},
        {"threshold": Range("NaN", "1", "0.1")},
        {"threshold": Range("1e-1000", "1", "0.1")},
        {"threshold": Range(0.1, 1, "0.1")},
        {"threshold": Range("0" * 200, "1", "0.1")},
        {"selected": Range(0, 100000, 1)},
        {"selected": [1, 2]},
        {"threshold": Range("1", "1.00000000000000002", "0.00000000000000001")},
    ],
)
def test_bad_domains(search):
    with pytest.raises((ValueError, TypeError)):
        plan(Scan, search, execution={"v": 1})


def test_domain_metadata_types_and_limits(monkeypatch):
    class Mode(Enum):
        ONE = 1
        TWO = 2

    class Kinds(Strategy):
        a = inputs.price(1.0, title="price")
        b = inputs.string("a", title="string", options=["a", "b"])
        c = inputs.session("24x7", title="session")
        d = inputs.color("#ffffff", title="color")
        e = inputs.time(1, title="time")
        f = inputs.enum(Mode.ONE, title="enum")
        g = inputs.bool(True, title="bool", active=False)

        def init(self):
            pass

        def next(self):
            pass

    values = {
        "price": Range("1", "2", "1"),
        "string": Values(["a", "b"]),
        "session": Values(["24x7"]),
        "color": Values(["#ff0000"]),
        "time": Values([1, 2]),
        "enum": Values([Mode.ONE, "TWO"]),
        "bool": Values([False]),
    }
    p = plan(Kinds, values, execution={"v": 1})
    assert p.total == 16
    for search in (
        {"string": Values(["c"])},
        {"enum": Values(["INVALID"])},
        {"session": Values(["24x7", "0000-0000:1234567"])},
        {"color": Values(["#ffffff", "#FFFFFFFF"])},
        {"bool": Values([1])},
    ):
        with pytest.raises(ValueError):
            plan(Kinds, search, execution={"v": 1})
    import importlib

    module = importlib.import_module("openbacktesting.optimizer.plan")
    monkeypatch.setattr(module, "MAX_TOTAL", 1)
    with pytest.raises(ValueError, match="combination count"):
        basic_plan()
    for execution in ({}, None):
        with pytest.raises(ValueError):
            plan(Scan, {"selected": Values([1])}, execution=execution)
    for constraint_id in ("", 1):
        with pytest.raises(ValueError):
            basic_plan(constraint_id=constraint_id)
    with pytest.raises(ValueError):
        encode({1: "bad"})
    with pytest.raises(ValueError):
        ExecutionIdentity("bad", "b" * 64)


def test_real_execution_only_portfolio_and_query(tmp_path):
    seen = []
    original = kwargs()

    def progress(event):
        saved = open_result(tmp_path / "results.db")
        seen.append(saved.info()["committed"])
        assert saved.load_portfolio(event["trial_id"])["context"]["inputs"]["values"]["fixed"] == 99
        original["data"].iloc[:, :] = 1
        original["request"]["values"]["fixed"] = 1

    result = launch(tmp_path, **(original | {"on_progress": progress}))
    assert seen == [1, 2, 3] and result.info()["status"] == "completed"
    for trial in result.trials():
        saved = result.load_portfolio(trial["trial_id"])
        assert saved["context"]["inputs"]["values"]["fixed"] == 99
        assert "strategy_logs" not in encode(saved) and "plotting_result" not in encode(saved)
    assert result.fields()
    sorted_rows = result.query(
        order_by=["summary.all.totalReturn.value"], fields=["summary.all.maxDrawdownFraction.value"]
    )["rows"]
    assert len(sorted_rows) == 3
    legacy = next(
        f["path"]
        for f in result.fields()
        if "Max\\. Drawdown" in f["path"] and f["path"].endswith(".value")
    )
    assert len(result.query(order_by=[(legacy, "desc")])["rows"]) == 3
    first = result.query(limit=1)
    second = result.query(limit=1, cursor=first["cursor"])
    assert first["rows"][0]["ordinal"] == 0 and second["rows"][0]["ordinal"] == 1
    assert result.query(filters=[("summary.all.totalReturn.value", "ge", -1)])["rows"]
    assert not result.query(filters=[("summary.all.totalReturn.value", "gt", 999)])["rows"]
    backup = result.backup(tmp_path / "copy.db")
    assert open_result(backup).query() == result.query()
    with pytest.raises(FileExistsError):
        result.backup(backup)
    with pytest.raises(ValueError):
        open_result(backup, "bad")
    with pytest.raises(OptimizationError):
        launch(tmp_path)


def test_zero_failed_cancel_resume_and_constraints(tmp_path):
    empty = launch(tmp_path, request=request_for(Scan, {"fixed": 99, "enabled": False}))
    assert all(
        empty.load_portfolio(t["trial_id"])["summary"]["all"]["closedFragmentCount"]["value"] == 0
        for t in empty.trials()
    )
    failed = optimize(
        namespace(), {"selected": Values([-1, 1])}, path=tmp_path / "failed.db", **kwargs()
    )
    assert failed.info()["status"] == "completed_with_errors" and failed.info()["failed"] == 1
    path = tmp_path / "cancel.db"
    events = []
    partial = optimize(
        namespace(),
        {"selected": Values([1, 2, 3])},
        path=path,
        **kwargs(),
        cancel=lambda: bool(events),
        on_progress=events.append,
    )
    assert partial.info()["status"] == "cancelled" and partial.info()["committed"] == 1
    completed = resume_optimization(
        namespace(), path=path, experiment_id=partial.experiment_id, **kwargs()
    )
    assert completed.info()["committed"] == 3
    assert [t["attempt"] for t in completed.trials()] == [1, 1, 1]
    bad = kwargs()
    bad["data"].iloc[0, 0] += 1
    with pytest.raises(OptimizationError, match="does not match"):
        resume_optimization(namespace(), path=path, experiment_id=partial.experiment_id, **bad)
    skipped = optimize(
        namespace(),
        {"selected": Values([1, 2])},
        path=tmp_path / "skip.db",
        **kwargs(),
        constraint=lambda values: values["fixed"] < 0,
        constraint_id="v1",
    )
    assert skipped.info()["status"] == "completed" and skipped.info()["skipped"] == 2
    assert not skipped.query()["rows"]
    for i, constraint in enumerate((lambda _: 1, lambda _: 1 / 0)):
        with pytest.raises(OptimizationError):
            optimize(
                namespace(),
                {"selected": Values([1])},
                path=tmp_path / f"bad{i}.db",
                **kwargs(),
                constraint=constraint,
                constraint_id="v1",
            )


@pytest.mark.parametrize(
    "query",
    [
        {"limit": 0},
        {"limit": True},
        {"order_by": [("a", "bad")]},
        {"filters": [("a", "bad", 1)]},
        {"fields": ["missing"]},
        {"fields": ["series.account"]},
        {"cursor": "{}"},
        {"filters": [("summary.all.totalReturn.value", "gt", None)]},
        {"filters": [("summary.all.totalReturn.value", "gt", "NaN")]},
    ],
)
def test_query_errors(tmp_path, query):
    result = launch(tmp_path)
    with pytest.raises(ValueError):
        result.query(**query)
    with pytest.raises(ValueError):
        result.trials(offset=-1)
    with pytest.raises(ValueError):
        result.load_portfolio("missing")


def test_store_atomic_conflicts_corruption(tmp_path):
    p = basic_plan()
    with owner(tmp_path / "store.db"):
        with pytest.raises(sqlite3.OperationalError), owner(tmp_path / "store.db"):
            pass
        store = Store(tmp_path / "store.db", p)
        req = next(iter(combinations(p)))[1]
        trial, attempt = store.start(0, req)
        payload = report(req)
        with pytest.raises(ValueError):
            store.commit(trial, attempt, payload)
        store.state(trial, attempt, "persisting")
        wrong = copy.deepcopy(payload)
        wrong["context"]["inputs"]["values"]["selected"] = 99
        with pytest.raises(ValueError, match="parameter"):
            store.commit(trial, attempt, wrong)
        store.commit(trial, attempt, payload)
        store.commit(trial, attempt, payload)
        wrong = copy.deepcopy(payload)
        wrong["diagnostics"].append("changed")
        with pytest.raises(ValueError, match="conflict"):
            store.commit(trial, attempt, wrong)
        with pytest.raises(ValueError):
            store.commit(trial, attempt + 1, payload)
        with pytest.raises(ValueError):
            store.state(trial, attempt, "failed")
        store.conn.execute("UPDATE trials SET report='{}' WHERE id=?", (trial,))
        store.conn.commit()
        with pytest.raises(ValueError, match="verification"):
            open_result(store.path).load_portfolio(trial)
        store.close()
    conn = connect(tmp_path / "store.db")
    conn.execute("PRAGMA user_version=999")
    conn.close()
    with pytest.raises(ValueError, match="version"):
        open_result(tmp_path / "store.db")


def test_shared_contract_cases():
    fixture = json.loads((ROOT / "tests/fixtures/portfolio.json").read_text())
    for value in fixture["valid"]:
        assert validate_report(value) is value
    for case in fixture["invalid"]:
        value = copy.deepcopy(fixture["valid"][case["base"]])
        current = value
        for part in case["path"][:-1]:
            current = current[part]
        current[case["path"][-1]] = case["value"]
        with pytest.raises(ValueError):
            validate_report(value)
    assert next(iter(flatten({"durationNs": "9007199254740993"})))[2] == "number"


def test_execution_failure_boundaries(tmp_path, monkeypatch):
    from openbacktesting.optimizer import runner

    p = basic_plan()
    with pytest.raises(ValueError):
        execute(p, report, tmp_path / "a.db", constraint=lambda _: True)

    def bad_progress(_):
        raise RuntimeError("callback")

    with pytest.raises(OptimizationError, match="callback") as caught:
        execute(p, report, tmp_path / "callback.db", on_progress=bad_progress)
    assert caught.value.committed == 1
    assert open_result(tmp_path / "callback.db").info()["committed"] == 1
    original = runner.Store.commit

    def fail_commit(*_):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(runner.Store, "commit", fail_commit)
    with pytest.raises(OptimizationError, match="disk full"):
        execute(p, report, tmp_path / "disk.db")
    assert open_result(tmp_path / "disk.db").info()["committed"] == 0
    monkeypatch.setattr(runner.Store, "commit", original)
    recovered = execute(
        p,
        report,
        tmp_path / "disk.db",
        experiment_id=open_result(tmp_path / "disk.db").experiment_id,
    )
    assert recovered.info()["committed"] == 2 and recovered.trials()[0]["attempt"] == 2


def test_identity_rejects_unstable_material_and_changes():
    from openbacktesting.optimizer.identity import execution_identity

    frame = data()
    original = execution_identity(frame, IDENTITY, {})
    assert original == execution_identity(frame.copy(), IDENTITY, {})
    frame.index = frame.index.tz_convert("Asia/Shanghai")
    assert original != execution_identity(frame, IDENTITY, {})
    for bad_frame, identity in [
        (data(), None),
        ([], IDENTITY),
        (data().reset_index(drop=True), IDENTITY),
    ]:
        with pytest.raises(TypeError):
            execution_identity(bad_frame, identity, {})
    frame = data()
    frame["objects"] = [{}, {}, {}, {}]
    with pytest.raises(TypeError):
        execution_identity(frame, IDENTITY, {})
    frame = data()
    frame.columns = ["a", "a", "c", "d"]
    with pytest.raises(ValueError):
        execution_identity(frame, IDENTITY, {})
    frame.columns = [1, 2, 3, 4]
    with pytest.raises(ValueError):
        execution_identity(frame, IDENTITY, {})


def test_query_precision_nulls_status_and_live_snapshot(tmp_path):
    p = basic_plan({"selected": Values([1, 2, 3])})
    path = tmp_path / "query.db"

    def custom(req):
        value = report(req)
        n = req["values"]["selected"]
        value["extensions"]["legacy"]["huge"] = {
            "value": str(9007199254740995 - n),
            "unit": "ns",
            "status": "ok",
            "methodId": "test",
            "sampleCount": None,
            "reason": None,
            "reference": None,
        }
        value["extensions"]["legacy"]["nullable"] = {
            "value": None if n == 1 else 2,
            "unit": "ratio",
            "status": "undefined" if n == 1 else "approximate",
            "methodId": "test",
            "sampleCount": None,
            "reason": "unbounded" if n == 1 else None,
            "reference": None,
        }
        return value

    store = Store(path, p)
    iterator = iter(combinations(p))

    def commit_next():
        ordinal, request = next(iterator)
        trial, attempt = store.start(ordinal, request)
        store.state(trial, attempt, "persisting")
        store.commit(trial, attempt, custom(request))

    commit_next()
    commit_next()
    result = open_result(path)
    first = result.query(limit=1)
    commit_next()
    second = result.query(limit=1, cursor=first["cursor"])
    assert second["cursor"] is None and second["watermark"] == 2
    assert result.query()["watermark"] == 3
    key = "extensions.legacy.huge.value"
    assert [r["inputs"]["selected"] for r in result.query(order_by=[(key, "asc")])["rows"]] == [
        3,
        2,
        1,
    ]
    assert len(result.query(filters=[(key, "eq", "9007199254740993")])["rows"]) == 1
    nullable = "extensions.legacy.nullable.value"
    assert result.query(order_by=[nullable])["rows"][-1]["inputs"]["selected"] == 1
    assert len(result.query(filters=[(nullable, "status", "undefined")])["rows"]) == 1
    assert (
        len(
            result.query(
                order_by=["context.timezone"], filters=[("context.timezone", "eq", "UTC")]
            )["rows"]
        )
        == 3
    )
    assert len(result.query(filters=[("run.complete", "eq", True)])["rows"]) == 3
    store.conn.execute(
        "UPDATE scalars SET method='changed' WHERE path=? AND trial LIKE '%:0'", (key,)
    )
    store.conn.commit()
    with pytest.raises(ValueError, match="statistical definitions"):
        result.query(order_by=[key])
    store.close()


def test_validation_rejects_structural_damage():
    from openbacktesting.optimizer.validation import _valid

    fixture = json.loads((ROOT / "tests/fixtures/portfolio.json").read_text())["valid"][0]
    for patch in (
        {"schemaVersion": "bad"},
        {"extra": 1},
        {"facts": []},
        {"diagnostics": [float("inf")]},
        {"run": {}},
        {"diagnostics": [object()]},
    ):
        with pytest.raises((ValueError, TypeError)):
            validate_report(fixture | patch)
    assert not _valid("bad", {"enum": ["good"]})
    assert not _valid([], {"minItems": 1})
    assert not _valid([1], {"items": {"type": "string"}})
    assert not _valid({"a": 1}, {"properties": {"a": {"type": "string"}}})
    assert not _valid(1, {"anyOf": [{"type": "string"}]})


def test_io_errors_keep_result_and_cleanup(tmp_path, monkeypatch):
    from openbacktesting.optimizer import runner, storage
    from openbacktesting.optimizer.query import ExperimentResult

    for bad in (":memory:", "file:/tmp/test", "//remote/test"):
        with pytest.raises(ValueError):
            connect(bad)
    result = launch(tmp_path)
    with pytest.raises(ValueError):
        ExperimentResult(result.path, "wrong").info()
    target = tmp_path / "backup.db"
    with pytest.raises(ValueError):
        ExperimentResult(result.path, "wrong").backup(target)
    assert not target.exists()
    p = basic_plan()

    def failed(*_):
        raise sqlite3.OperationalError("offline")

    monkeypatch.setattr(runner.Store, "commit", failed)
    monkeypatch.setattr(runner.Store, "finish", failed)
    with pytest.raises(OptimizationError, match="Failed to persist experiment failure status"):
        execute(p, report, tmp_path / "fail.db")
    original = storage.connect

    class BadPragma:
        def __init__(self, conn):
            self.conn = conn

        def execute(self, query, *args):
            if query == "PRAGMA journal_mode=WAL":
                return self.conn.execute("SELECT 'delete'")
            return self.conn.execute(query, *args)

        def __getattr__(self, name):
            return getattr(self.conn, name)

    monkeypatch.setattr(storage, "connect", lambda path: BadPragma(original(path)))
    with pytest.raises(RuntimeError, match="durability"):
        storage.Store(tmp_path / "pragma.db", p)


def test_config_validation_and_constraint_true(tmp_path):
    p = basic_plan(constraint_id="v1")
    result = execute(p, report, tmp_path / "yes.db", constraint=lambda _: True)
    assert result.info()["committed"] == 2
    bad = kwargs()
    bad["context"] = None
    with pytest.raises(TypeError):
        launch(tmp_path, **bad)
    for key in ("schemaHash", "schemaVersion"):
        request = request_for(Scan, {})
        request[key] = "bad"
        with pytest.raises(ValueError):
            basic_plan(base_inputs=request)
    p = plan(Scan, {"selected": Values([1])}, execution={"backtest": {"settings": {"bad": 1}}})
    with pytest.raises(OptimizationError, match="configuration"):
        execute(p, report, tmp_path / "wrong.db")
    # Restored Range expressions must preserve decimal/integer origins rather than becoming a different plan.
    first = optimize(
        namespace(),
        {"selected": Range(1, 2, 1)},
        path=tmp_path / "range.db",
        **kwargs(),
        cancel=lambda: True,
    )
    assert (
        resume_optimization(
            namespace(), path=first.path, experiment_id=first.experiment_id, **kwargs()
        ).info()["committed"]
        == 2
    )


def test_twelve_runs_and_export_failure(tmp_path, monkeypatch):
    from openbacktesting.portfolio import snapshot

    calls = []
    original = Scan.init

    def initialized(self):
        calls.append((self.selected, self.threshold, self.enabled))
        original(self)

    monkeypatch.setattr(Scan, "init", initialized)
    result = optimize(
        namespace(),
        {
            "selected": Range(1, 2, 1),
            "threshold": Range("0.1", "0.3", "0.1"),
            "enabled": Values([True, False]),
        },
        path=tmp_path / "twelve.db",
        **kwargs(),
    )
    assert len(calls) == len(set(calls)) == result.info()["committed"] == 12
    original_export = snapshot.export_result

    def bad_export(stats):
        if stats.attrs["input_snapshot"]["values"]["selected"] == 1:
            raise ValueError("export failed")
        return original_export(stats)

    monkeypatch.setattr(snapshot, "export_result", bad_export)
    failed = launch(tmp_path)
    assert failed.info()["failed"] == 1 and failed.info()["committed"] == 2
    assert failed.trials()[0]["error"].startswith("export:")


def test_invalid_export_continues_and_transaction_rolls_back(tmp_path):
    p = basic_plan()
    result = execute(
        p, lambda req: {} if req["values"]["selected"] == 1 else report(req), tmp_path / "export.db"
    )
    assert result.info()["failed"] == result.info()["committed"] == 1
    assert result.trials()[0]["error"].startswith("export:")
    store = Store(tmp_path / "rollback.db", p)
    for ordinal, req in combinations(p):
        trial, attempt = store.start(ordinal, req)
        store.state(trial, attempt, "persisting")
        payload = report(req)
        if ordinal == 0:
            store.commit(trial, attempt, payload)
        else:
            store.conn.execute(
                "CREATE TRIGGER disk_full BEFORE INSERT ON scalars BEGIN SELECT RAISE(ABORT, 'disk full'); END"
            )
            with pytest.raises(sqlite3.IntegrityError, match="disk full"):
                store.commit(trial, attempt, payload)
            saved = open_result(store.path)
            assert saved.info()["committed"] == 1 and saved.query()["watermark"] == 1
            assert (
                store.conn.execute("SELECT report FROM trials WHERE id=?", (trial,)).fetchone()[0]
                is None
            )
            assert saved.load_portfolio(saved.trials()[0]["trial_id"])
    store.close()


def test_reader_backup_and_cancel_while_next_trial_runs(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    started, release, cancelled = Event(), Event(), Event()
    original = Scan.next

    def blocked(self):
        if self.selected == 2 and self.bar_index == 0:
            started.set()
            assert release.wait(10)
        original(self)

    monkeypatch.setattr(Scan, "next", blocked)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(launch, tmp_path, cancel=cancelled.is_set)
        try:
            assert started.wait(10)
            saved = open_result(tmp_path / "results.db")
            assert saved.info()["committed"] == 1 and saved.info()["running"] == 1
            first_id = saved.trials()[0]["trial_id"]
            payload = saved.load_portfolio(first_id)
            payload["diagnostics"].append("mutated reader copy")
            assert payload != saved.load_portfolio(first_id)
            backup = open_result(saved.backup(tmp_path / "live-backup.db"))
            assert backup.info()["committed"] == 1
            assert backup.load_portfolio(first_id) == saved.load_portfolio(first_id)
            cancelled.set()
        finally:
            release.set()
        result = future.result(timeout=10)
    assert result.info()["committed"] == 2 and result.info()["remaining"] == 1
    assert result.info()["status"] == "cancelled"


def test_bankruptcy_and_plain_run_collection(tmp_path):
    @backtest(cash=1000, margin=0.1)
    class Bankrupt(Strategy):
        quantity = inputs.int(20, title="quantity")

        def init(self):
            self.log.info("kept in normal run")

        def next(self):
            self.plotting.bg_color("#123456")
            if len(self.data) == 2:
                self.buy(qty=self.quantity)

    prices = [100.0] * 3 + [1.0] * 5
    frame = pd.DataFrame(
        {k: prices for k in ("Open", "High", "Low", "Close")},
        index=pd.date_range("2026-01-01", periods=8, tz="UTC"),
    )
    opts = {"data": frame, "context": CONTEXT, "instrument": InstrumentSpec()}
    ordinary = run(namespace(Bankrupt), **opts)
    assert ordinary.attrs["strategy_logs"] and ordinary.attrs["plotting_result"]
    saved = optimize(
        namespace(Bankrupt),
        {"quantity": Values([20])},
        path=tmp_path / "insolvent.db",
        identity=IDENTITY,
        **opts,
    )
    payload = saved.load_portfolio(saved.trials()[0]["trial_id"])
    assert saved.info()["committed"] == 1
    assert payload["run"]["terminationReason"] == "insolvent" and not payload["run"]["complete"]
    assert "strategy_logs" not in payload and "plotting_result" not in payload


def test_schema_keywords_match_independent_validator():
    from openbacktesting.optimizer.validation import _schema

    supported = {
        "$defs",
        "$ref",
        "$schema",
        "additionalProperties",
        "anyOf",
        "const",
        "enum",
        "items",
        "maxItems",
        "minItems",
        "oneOf",
        "properties",
        "required",
        "title",
        "type",
    }

    def check(schema):
        assert set(schema) <= supported, (
            "New Schema keywords must extend the standalone package checker"
        )
        for key in ("$defs", "properties"):
            for child in schema.get(key, {}).values():
                check(child)
        for key in ("anyOf", "oneOf"):
            for child in schema.get(key, []):
                check(child)
        for key in ("items", "additionalProperties"):
            if isinstance(schema.get(key), dict):
                check(schema[key])

    check(_schema())


def test_resume_checks_each_identity_material(tmp_path, monkeypatch):
    from openbacktesting.optimizer import identity as identity_module

    saved = launch(tmp_path, cancel=lambda: True)
    original = kwargs()
    alternatives = [
        original | {"identity": ExecutionIdentity("c" * 64, "b" * 64)},
        original | {"identity": ExecutionIdentity("a" * 64, "c" * 64)},
        original | {"settings": {"cash": 20000}},
        original | {"request": request_for(Scan, {"fixed": 98})},
        original | {"constraint": lambda _: True, "constraint_id": "new"},
        original | {"context": DataContext(Timeframe(TimeframeUnit.DAY, 1), "Asia/Shanghai")},
    ]
    frame = data().astype("float32")
    alternatives.append(original | {"data": frame})
    for alternative in alternatives:
        with pytest.raises(OptimizationError, match="does not match"):
            resume_optimization(
                namespace(), path=saved.path, experiment_id=saved.experiment_id, **alternative
            )
    monkeypatch.setattr(identity_module.platform, "python_version", lambda: "different")
    with pytest.raises(OptimizationError, match="does not match"):
        resume_optimization(
            namespace(), path=saved.path, experiment_id=saved.experiment_id, **original
        )
    assert saved.info()["checked"] == 0


def test_missing_null_and_scalar_status_are_distinct(tmp_path):
    key = "extensions.legacy.optional.value"

    def custom(req):
        payload = report(req)
        n = req["values"]["selected"]
        if n != 1:
            payload["extensions"]["legacy"]["optional"] = {
                "value": None if n == 2 else 3,
                "unit": "ratio",
                "status": "unsupported" if n == 2 else "ok",
                "methodId": "test",
                "sampleCount": None,
                "reason": "not supported" if n == 2 else None,
                "reference": None,
            }
        return payload

    result = execute(basic_plan({"selected": Values([1, 2, 3])}), custom, tmp_path / "status.db")
    rows = result.query(order_by=[key])["rows"]
    assert [row["inputs"]["selected"] for row in rows] == [3, 1, 2]
    assert [row["values"][key]["status"] for row in rows] == ["ok", "missing", "unsupported"]
    assert len(result.query(filters=[(key, "status", "missing")])["rows"]) == 1
    assert not result.query(filters=[("context.timezone", "status", "missing")])["rows"]
    assert len(result.query(filters=[("context.timezone", "status", "ok")])["rows"]) == 3
    assert len(result.query()["rows"]) == 3


def test_permission_error_reports_location(tmp_path, monkeypatch):
    from openbacktesting.optimizer import storage

    def denied(*args, **kwargs):
        raise PermissionError("permission denied")

    monkeypatch.setattr(storage, "connect", denied)
    path = tmp_path / "denied.db"
    with pytest.raises(OptimizationError, match="permission denied") as caught:
        execute(basic_plan(), report, path)
    assert caught.value.path == str(path) and caught.value.committed == 0


def test_analysis_drawdown_direction_and_duration_precision(tmp_path):
    from openbacktesting.optimizer.query import _direction

    assert _direction("analysis.equityMovements.summary.drawdown.maximumFraction") == "asc"
    assert _direction("extensions.legacy.Max\\. Drawdown [%].value") == "desc"
    assert next(flatten({"averageDurationNs": "9007199254740993"}))[2:4] == ("number", "ns")
    result = launch(tmp_path)
    fields = result.fields()
    key = next(f["path"] for f in fields if ".summary.drawdown.maximum" in f["path"])
    assert next(f for f in fields if f["path"] == key)["suggestedDirection"] == "asc"
    assert result.query(order_by=[key]) == result.query(order_by=[(key, "asc")])
    # Isolate precision using a valid nanosecond report-export field while retaining full report validation and transactional projection.
    path = next(f["path"] for f in fields if f["path"].endswith("averageDurationNs"))

    def custom(req):
        payload = report(req)
        node = payload
        parts = path.split(".")
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = ["10", "2", "9007199254740993"][req["values"]["selected"] - 1]
        return payload

    precise = execute(
        basic_plan({"selected": Values([1, 2, 3])}), custom, tmp_path / "durations.db"
    )
    assert [row["ordinal"] for row in precise.query(order_by=[(path, "asc")])["rows"]] == [1, 0, 2]


def test_all_null_metrics_keep_units_and_methods(tmp_path):
    result = launch(tmp_path, request=request_for(Scan, {"enabled": False}))
    field = next(f for f in result.fields() if f["kind"] == "null" and f["unit"] and f["method"])
    rows = result.query(fields=[field["path"]])["rows"]
    assert len(rows) == 3
    for row in rows:
        value = row["values"][field["path"]]
        assert value["value"] is None
        assert value["unit"] == field["unit"] and value["methodId"] == field["method"]
    conn = connect(result.path)
    conn.execute(
        "UPDATE scalars SET method='other' WHERE path=? AND trial=?",
        (field["path"], rows[0]["trial_id"]),
    )
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="statistical definitions"):
        result.query(order_by=[field["path"]])


def test_core_identity_reads_historical_results_but_rejects_cross_identity_resume(
    tmp_path, monkeypatch
):
    from importlib.metadata import version

    from openbacktesting.optimizer import identity as identity_module

    original = identity_module.execution_identity

    def historical(*args):
        value = original(*args)
        value["environment"]["previous_distribution"] = value["environment"].pop("openbacktesting")
        return value

    with monkeypatch.context() as patch:
        patch.setattr(identity_module, "execution_identity", historical)
        saved = launch(tmp_path)
    before = Path(saved.path).read_bytes()
    reopened = open_result(saved.path)
    assert len(reopened.query(order_by=["summary.all.totalReturn.value"])["rows"]) == 3
    assert reopened.load_portfolio(reopened.trials()[0]["trial_id"])["summary"]
    with pytest.raises(OptimizationError, match="does not match"):
        resume_optimization(
            namespace(), path=saved.path, experiment_id=saved.experiment_id, **kwargs()
        )
    assert Path(saved.path).read_bytes() == before
    execution = original(data(), IDENTITY, {})
    assert execution["environment"]["openbacktesting"] == version("openbacktesting")
    assert "previous_distribution" not in execution["environment"]
    current = optimize(
        namespace(),
        {"selected": Values([1, 2])},
        path=tmp_path / "current.db",
        cancel=lambda: True,
        **kwargs(),
    )
    restored = resume_optimization(
        namespace(), path=current.path, experiment_id=current.experiment_id, **kwargs()
    )
    assert restored.info()["committed"] == 2


def test_real_ema_report_has_only_plain_values_and_can_be_optimized(tmp_path):
    import runpy

    from openbacktesting.portfolio import export_result
    from openbacktesting.test import GOOG

    ns = runpy.run_path(str(ROOT / "examples/strategies/ema_inputs.py"))
    ns["__name__"] = ns["EmaCross"].__module__
    market = GOOG.copy()
    market.index = market.index.tz_localize("UTC")
    config = {"data": market, "context": CONTEXT, "instrument": InstrumentSpec(symbol="GOOG")}
    report = export_result(
        run(
            ns,
            request_for(
                ns["EmaCross"], {"fast": 12, "slow": 26, "units": 1, "short_enabled": False}
            ),
            options={"plotting": False},
            **config,
        )
    )

    def assert_plain(value):
        assert type(value) in (dict, list, str, int, float, bool, type(None))
        if isinstance(value, dict):
            for child in value.values():
                assert_plain(child)
        elif isinstance(value, list):
            for child in value:
                assert_plain(child)

    # IQR outlier bounds previously leaked numpy.float64 and failed optimizer validation.
    assert_plain(report)
    assert type(report["analysis"]["distribution"]["outliers"]["lower"]) is float
    experiment = optimize(
        ns, {"Fast period": Values([12, 13])}, path=tmp_path / "ema.db", identity=IDENTITY, **config
    )
    assert experiment.info()["committed"] == 2
    assert experiment.info()["failed"] == 0
    saved = experiment.load_portfolio(experiment.trials()[0]["trial_id"])
    assert saved == report
