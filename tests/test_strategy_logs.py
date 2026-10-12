"""Strategy-log fields, source locations, lifecycles, and backtest-output isolation."""

import gc
import inspect
import json
import logging
import pickle
import weakref
from datetime import UTC, datetime
from types import SimpleNamespace

import pandas as pd
import pytest
from test_engine_edges import Idle, flat_data
from test_input_runtime import TradingInputs, compare
from test_inputs import request

from openbacktesting import Backtest, inputs
from openbacktesting import logs as log_module
from openbacktesting.logs import StrategyLog, _Collector
from openbacktesting.simulation import core


def test_levels_locations_full_history_and_copies(monkeypatch):
    collector = _Collector()
    log = StrategyLog(collector)
    with collector.phase("next", 12, "2025-01-01T00:00:00+08:00", "aware-datetime"):
        line = inspect.currentframe().f_lineno + 1
        assert log.info("") is None
        log.warning("中文\n第二行")
        log.error("Continue")
        for _ in range(10001):
            log.info("duplicate")
        for value in (None, 1, ValueError("Not a string")):
            with pytest.raises(TypeError, match="string"):
                log.info(value)
    records = collector.snapshot()
    assert len(records) == 10004
    assert [r["sequence"] for r in records] == list(range(1, 10005))
    assert [r["level"] for r in records[:3]] == ["info", "warning", "error"]
    assert [r["message"] for r in records[:3]] == ["", "中文\n第二行", "Continue"]
    assert [r["source_line"] for r in records[:3]] == [line, line + 1, line + 2]
    assert records[0]["source_file"] == __file__
    assert records[0]["bar_index"] == 12
    assert records[0]["phase"] == "next"
    assert set(records[0]) == {
        "sequence",
        "level",
        "message",
        "phase",
        "bar_index",
        "bar_time",
        "time_kind",
        "recorded_at",
        "source_file",
        "source_line",
    }
    assert datetime.fromisoformat(records[0]["recorded_at"]).tzinfo == UTC
    json.dumps(records, allow_nan=False)
    records[0]["message"] = "Modified copy"
    records.pop()
    assert collector.snapshot()[0]["message"] == ""
    with pytest.raises(RuntimeError, match="active"):
        log.info("Outside callback")
    collector.close()
    with pytest.raises(RuntimeError, match="ended"), collector.phase("next"):
        pytest.fail("A closed session cannot be reentered")


@pytest.mark.parametrize(
    "frame",
    [
        None,
        SimpleNamespace(f_back=None),
        SimpleNamespace(f_back=SimpleNamespace(f_back=None)),
        SimpleNamespace(
            f_back=SimpleNamespace(
                f_back=SimpleNamespace(f_code=SimpleNamespace(co_filename=""), f_lineno=1)
            )
        ),
        SimpleNamespace(
            f_back=SimpleNamespace(
                f_back=SimpleNamespace(f_code=SimpleNamespace(co_filename="file"), f_lineno=0)
            )
        ),
    ],
)
def test_unknown_location_keeps_log(monkeypatch, frame):
    monkeypatch.setattr(log_module, "_currentframe", lambda: frame)
    collector = _Collector()
    with collector.phase("init"):
        StrategyLog(collector).info("Still retained")
    record = collector.snapshot()[0]
    assert record["source_file"] is record["source_line"] is None
    assert record["message"] == "Still retained"


def test_virtual_helper_inherited_multiline_without_source_io(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Must not read source or scan the complete stack")

    monkeypatch.setattr(inspect, "stack", forbidden)
    monkeypatch.setattr("linecache.getlines", forbidden)
    namespace = {}
    exec(  # noqa: S102 — fixed test source
        compile(
            'class Base:\n def emit(self, log):\n  log.warning(\n   "Cross-module"\n  )\nclass Child(Base): pass\n',
            "<virtual-strategy>",
            "exec",
        ),
        namespace,
    )
    collector = _Collector()
    with collector.phase("next", 0):
        namespace["Child"]().emit(StrategyLog(collector))
    assert collector.snapshot()[0]["source_file"] == "<virtual-strategy>"
    assert collector.snapshot()[0]["source_line"] == 3


def test_no_frame_retention_and_clock_order(monkeypatch):
    moments = iter([datetime(2025, 1, 2, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC)])
    monkeypatch.setattr(log_module, "_datetime", SimpleNamespace(now=lambda tz: next(moments)))
    collector = _Collector()
    log = StrategyLog(collector)

    class Payload:
        pass

    def emit():
        payload = Payload()
        ref = weakref.ref(payload)
        log.info("First record")
        return ref

    gc.disable()
    try:
        with collector.phase("next", 0):
            ref = emit()
            assert ref() is None  # Reclaim author locals without requiring GC.
            log.info("Second record")
    finally:
        gc.enable()
    records = collector.snapshot()
    assert records[0]["recorded_at"] > records[1]["recorded_at"]
    assert [r["sequence"] for r in records] == [1, 2]


def test_disabled_still_validates_without_location_or_clock(monkeypatch):
    def forbidden():
        raise AssertionError("Disabled collection must not read stack frames")

    monkeypatch.setattr(log_module, "_currentframe", forbidden)
    collector = _Collector(enabled=False)
    log = StrategyLog(collector)
    with collector.phase("init"):
        assert log.info("Not retained") is None
        with pytest.raises(TypeError):
            log.error(1)
    with pytest.raises(RuntimeError):
        log.warning("Still rejected outside callback")
    assert collector.snapshot() == []


class LoggingTrade(TradingInputs):
    def init(self):
        super().init()
        self.log.info("Initialization")

    def on_start(self):
        self.log.info("Start")

    def next(self):
        self.log.info(f"Quantity={self.units}")
        super().next()

    def on_order(self, event):
        self.log.warning(event.snapshot.status.value)

    def on_fill(self, event):
        self.log.info("Fill")

    def on_finish(self, summary):
        self.log.error(summary.reason)


@pytest.mark.parametrize("kind", ["aware", "naive", "ordinal"])
@pytest.mark.parametrize("count", [1, 6])
def test_lifecycle_time_and_query_copies(kind, count):
    data = flat_data(count)
    if kind == "aware":
        data.index = data.index.tz_localize("Asia/Shanghai") + pd.Timedelta(123, "ns")
    elif kind == "ordinal":
        data.index = pd.RangeIndex(count)
    bt = Backtest(data, LoggingTrade, plotting=False)
    assert bt.get_logs() == []
    result = bt.run()
    records = bt.get_logs()
    assert result.attrs["strategy_logs"] == records
    assert records[0]["phase"] == "init" and records[-1]["phase"] == "on_finish"
    assert records[0]["bar_index"] is records[-1]["bar_index"] is None
    assert records[0]["time_kind"] == "none"
    for row in records[1:-1]:
        idx = row["bar_index"]
        assert (
            row["time_kind"]
            == {"aware": "aware-datetime", "naive": "naive-datetime", "ordinal": "ordinal"}[kind]
        )
        assert row["bar_time"] == (None if kind == "ordinal" else data.index[idx].isoformat())
    assert records[1]["bar_index"] == 0 and records[1]["phase"] == "on_start"
    assert [r["bar_index"] for r in records if r["phase"] == "next"] == list(range(count))
    if count > 1:
        assert {"on_order", "on_fill"} <= {r["phase"] for r in records}
    owner = result["_strategy"]
    with pytest.raises(RuntimeError):
        owner.log.info("Ended")
    restored = pickle.loads(pickle.dumps(result))
    assert restored.attrs["strategy_logs"] == records
    result.attrs["strategy_logs"][0]["message"] = "Override"
    records.clear()
    assert bt.get_logs()[0]["message"] == "Initialization"
    old = bt.get_logs()
    bt.run()
    assert old[0]["sequence"] == bt.get_logs()[0]["sequence"] == 1
    assert restored.attrs["strategy_logs"] == old


@pytest.mark.parametrize("phase", ["init", "next", "finish", "stats", "export"])
@pytest.mark.parametrize("double", [False, True])
def test_failure_preserves_logs_original_exception_and_closes(monkeypatch, phase, double):
    primary, secondary = ValueError("Primary exception"), RuntimeError("End exception")
    owners = []

    class Fail(Idle):
        def init(self):
            owners.append(self)
            self.log.info("init")
            if phase == "init":
                raise primary

        def next(self):
            self.log.info("next")
            if phase == "next":
                raise primary

        def on_finish(self, summary):
            self.log.info("finish")
            if phase == "finish":
                raise primary
            if double and phase in ("init", "next"):
                raise secondary

    if phase == "stats":

        def fail_stats(**kwargs):
            raise primary

        monkeypatch.setattr(core, "compute_stats", fail_stats)
    if phase == "export":

        def fail_export(*args):
            raise primary

        monkeypatch.setattr(core.Plotting, "_finish", fail_export)
    bt = Backtest(flat_data(2), Fail)
    with pytest.raises(ValueError) as caught:
        bt.run()
    assert caught.value is primary
    records = bt.get_logs()
    assert records[0]["message"] == "init" and records[-1]["message"] == "finish"
    assert sum(r["message"] == "finish" for r in records) == 1
    if double and phase in ("init", "next"):
        assert "End exception" in primary.__notes__[0]
    with pytest.raises(RuntimeError):
        owners[0].log.info("After end")


def test_reset_validation_constructor_and_custom_dispatch(monkeypatch):
    class Observed(Backtest):
        def run(self, **kwargs):
            self.calls = getattr(self, "calls", 0) + 1
            return super().run(**kwargs)

    bt = Observed(flat_data(6), LoggingTrade)
    native = bt.run()
    titled = bt.run_inputs(request(LoggingTrade, {"Quantity": 2}))
    assert bt.calls == 2
    assert titled.attrs["strategy_logs"][0]["sequence"] == 1
    saved = bt.get_logs()
    for invoke in [lambda: bt.run(unknown=1), lambda: bt.run_inputs({})]:
        with pytest.raises((AttributeError, inputs.InputError)):
            invoke()
        assert bt.get_logs() == []
    assert saved and native.attrs["strategy_logs"]
    with monkeypatch.context() as patcher:

        def fail(*args):
            raise ValueError("Construction failure")

        patcher.setattr(LoggingTrade, "__init__", fail)
        with pytest.raises(ValueError, match="Construction failure"):
            bt.run()
        assert bt.get_logs() == []
    assert bt.run().attrs["strategy_logs"]


@pytest.mark.parametrize("conflict", ["field", "method", "input", "inherited"])
def test_log_reserved_declarations(conflict):
    value = (
        inputs.int(1, title="Quantity")
        if conflict == "input"
        else (lambda self: None)
        if conflict == "method"
        else 3
    )
    cls = type("Conflict", (Idle,), {"log": value})
    if conflict == "inherited":
        cls = type("Inherited", (cls,), {})
    with pytest.raises((AttributeError, inputs.InputError), match="log"):
        Backtest(flat_data(), cls).run()


def test_log_reserved_instance_params_and_display_title():
    class Allowed(Idle):
        value = inputs.int(1, title="log")

        def next(self):
            assert self.log is self.log
            with pytest.raises(AttributeError, match="reserved attribute"):
                self.log = 1
            with pytest.raises(AttributeError, match="reserved attribute"):
                del self.log
            self.log.info(str(self.value))

    bt = Backtest(flat_data(1), Allowed)
    assert bt.run_inputs(request(Allowed, {"log": 2})).attrs["strategy_logs"][0]["message"] == "2"
    with pytest.raises(AttributeError, match="log"):
        Backtest(flat_data(), Idle).run(log=2)


def test_query_during_run_no_reentry_or_output_and_trading_unchanged(capsys):
    snapshots = []

    class Observe(LoggingTrade):
        def next(self):
            super().next()
            snapshots.append(bt.get_logs())
            with pytest.raises(RuntimeError, match="reentrantly"):
                bt.run()
            with pytest.raises(RuntimeError, match="reentrantly"):
                bt.optimize(units=[1])

    bt = Backtest(flat_data(6), Observe, plotting=False)
    before = logging.getLogger().level
    logging.getLogger().setLevel(logging.CRITICAL)
    try:
        result = bt.run()
    finally:
        logging.getLogger().setLevel(before)
    output = capsys.readouterr()
    assert "Initialization" not in output.out + output.err
    assert snapshots and len(snapshots[0]) < len(bt.get_logs())
    compare(result, Backtest(flat_data(6), TradingInputs, plotting=False).run())


def test_terminal_and_insolvency_use_actual_bar():
    class Hold(LoggingTrade):
        def next(self):
            self.log.info("next")
            if self.bar_index == 0:
                self.buy(qty=100)

    data = flat_data(4)
    data.loc[data.index[2] :, ["Open", "High", "Low", "Close"]] = 1.0
    bt = Backtest(data, Hold, cash=1000, margin=0.01)
    result = bt.run()
    records = bt.get_logs()
    assert result["Equity Final [$]"] == -8900
    terminal = [r for r in records if r["phase"].startswith("terminal_")]
    assert {r["phase"] for r in terminal} == {"terminal_order", "terminal_fill"}
    assert {r["bar_index"] for r in terminal} == {2}
    assert records[-1]["bar_index"] is None
    normal = Backtest(flat_data(3), Hold, cash=20000, end_policy="close_at_last_close")
    normal.run()
    assert {r["bar_index"] for r in normal.get_logs() if r["phase"].startswith("terminal_")} == {2}
