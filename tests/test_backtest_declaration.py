"""声明与图表上下文的公开行为和拒绝边界。"""

import json
import pickle
from abc import abstractmethod
from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pandas as pd
import pytest
from openbacktesting import (
    Backtest,
    CommissionType,
    DataContext,
    EndPolicy,
    ExecutionTiming,
    SlippageType,
    Strategy,
    Timeframe,
    TimeframeUnit,
    backtest,
    inputs,
    runtime,
)
from openbacktesting.broker import InstrumentSpec
from openbacktesting.simulation.config import BacktestSettings
from openbacktesting.strategy.declaration import declaration
from openbacktesting.test import GOOG


class Plain(Strategy):
    def init(self):
        self.initial_timeframe = self.timeframe

    def next(self):
        if len(self.data) == 2:
            self.buy(qty=1)
        elif len(self.data) == 4:
            self.close_position()


@backtest(cash=20_000, commission_value=0.2)
class Declared(Plain):
    length = inputs.int(2, title="长度")


class Inherited(Declared):
    pass


def namespace(cls=Declared):
    return {"__name__": cls.__module__, "strategy": cls}


def chart(**overrides):
    frame = GOOG.iloc[:12].copy()
    frame.index = frame.index.tz_localize("UTC")
    return {
        "data": frame,
        "context": DataContext(Timeframe.days(1), "UTC"),
        "instrument": InstrumentSpec(symbol="GOOG"),
    } | overrides


@pytest.mark.parametrize(
    "method,unit",
    [
        ("seconds", TimeframeUnit.SECOND),
        ("minutes", TimeframeUnit.MINUTE),
        ("days", TimeframeUnit.DAY),
        ("weeks", TimeframeUnit.WEEK),
        ("months", TimeframeUnit.MONTH),
    ],
)
def test_timeframe_values(method, unit):
    value = getattr(Timeframe, method)(7)
    assert value == Timeframe(unit, 7)
    assert hash(value) == hash(pickle.loads(pickle.dumps(value)))
    assert value.snapshot() == {"unit": unit.value, "multiplier": 7}
    with pytest.raises(FrozenInstanceError):
        value.multiplier = 2


@pytest.mark.parametrize("value", [True, False, 1.0, "2", None, 0, -1])
@pytest.mark.parametrize("make", [Timeframe.hours, Timeframe.minutes])
def test_invalid_multiplier(value, make):
    with pytest.raises((TypeError, ValueError)):
        make(value)


def test_calendar_units_and_context():
    assert Timeframe.hours(4) == Timeframe.minutes(240)
    assert Timeframe.hours(24) != Timeframe.days(1)
    assert Timeframe.days(7) != Timeframe.weeks(1)
    with pytest.raises(TypeError, match="TimeframeUnit"):
        Timeframe("minute", 1)
    context = DataContext(Timeframe.months(1), "Asia/Shanghai")
    assert pickle.loads(pickle.dumps(context)) == context
    snapshot = context.snapshot()
    snapshot["timeframe"]["multiplier"] = 99
    assert context.timeframe.multiplier == 1
    with pytest.raises(FrozenInstanceError):
        context.timezone = "UTC"
    with pytest.raises(TypeError, match="timeframe"):
        DataContext(None, "UTC")
    for invalid in (None, "", 1):
        with pytest.raises(TypeError, match="timezone"):
            DataContext(Timeframe.days(1), invalid)
    with pytest.raises(KeyError):
        DataContext(Timeframe.days(1), "Nowhere/Invalid")


def test_decorator_identity_defaults_and_inheritance():
    class Child(Plain):
        pass

    assert backtest()(Child) is Child
    assert declaration(Child) == BacktestSettings()
    assert declaration(Plain) is None and declaration(Inherited) is None
    assert runtime.discover(namespace(Child)) is Child
    assert declaration(Declared).cash == 20_000
    with pytest.raises(ValueError, match="重复"):
        backtest()(Child)
    with pytest.raises(FrozenInstanceError):
        declaration(Child).cash = 0
    Child._openbacktesting_backtest_settings = "corrupted"
    with pytest.raises(TypeError, match="声明"):
        runtime.discover(namespace(Child))


@pytest.mark.parametrize("target", [1, object, Strategy])
def test_invalid_decorator_target(target):
    with pytest.raises(TypeError, match="具体"):
        backtest()(target)


@pytest.mark.parametrize(
    "settings",
    [
        {"cash": 0},
        {"cash": True},
        {"cash": float("nan")},
        {"margin": 2},
        {"spread": -1},
        {"spread": 1},
        {"max_gross_exposure": 0},
        {"allow_short": 1},
        {"hedging": 0},
        {"exclusive_orders": None},
        {"execution_timing": "invalid"},
        {"end_policy": "invalid"},
        {"slippage": {}},
        {"commission": (1,)},
        {"commission": (-1, 0)},
        {"commission": (0, 0.1)},
        {"commission": True},
        {"commission": lambda q, p: 0},
        {"commission": [0, 0]},
        {"timeframe": Timeframe.days(1)},
        {"instrument": InstrumentSpec()},
        {"cash": None},
        {"commission": (True, 0)},
    ],
)
def test_settings_rejected(settings):
    with pytest.raises((TypeError, ValueError)):
        backtest(**settings)


def test_settings_overrides_and_export():
    initial = BacktestSettings(commission_value=-1, slippage_value=2, max_gross_exposure=2)
    resolved = initial.resolve(MappingProxyType({"cash": 12_000, "slippage_value": 0}))
    assert resolved.cash == 12_000 and resolved.slippage_value == 0
    assert resolved.commission_value == -1
    assert initial.slippage_value == 2
    assert initial.resolve({}) == initial.resolve(None)
    assert json.loads(json.dumps(initial.snapshot())) == initial.snapshot()
    for invalid in ([], False):
        with pytest.raises(TypeError, match="settings"):
            initial.resolve(invalid)
    with pytest.raises(ValueError, match="未知"):
        initial.resolve({"unknown": 1})


@pytest.mark.parametrize("value", [None, [], {}, {"__name__": ""}, {"__name__": 1}])
def test_invalid_namespace(value):
    with pytest.raises(TypeError):
        runtime.discover(value)


def test_discovery_selection_and_description(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("发现不能实例化")

    monkeypatch.setattr(Backtest, "__init__", forbidden)
    monkeypatch.setattr(Strategy, "__init__", forbidden)
    ns = namespace() | {
        "alias": Declared,
        "unmarked": Plain,
        "child": Inherited,
        "foreign": type("Imported", (Declared,), {"__module__": "elsewhere"}),
    }
    assert runtime.discover(MappingProxyType(ns)) is Declared
    exported = runtime.describe(ns)
    assert exported["backtest"]["settings"]["cash"] == 20_000
    assert exported["schemaHash"] == inputs.describe(Declared)["schemaHash"]
    exported["backtest"]["settings"]["cash"] = 1
    assert runtime.describe(ns)["backtest"]["settings"]["cash"] == 20_000
    with pytest.raises(ValueError, match="候选: \\[\\]"):
        runtime.discover({"__name__": "other", "strategy": Declared})

    @backtest()
    class Another(Plain):
        pass

    with pytest.raises(ValueError, match="Another"):
        runtime.discover(ns | {"other": Another})

    class Abstract(Plain):
        @abstractmethod
        def init(self):
            pass

    assert runtime.discover(ns | {"abstract": Abstract}) is Declared


def test_runtime_overrides_snapshot_isolation_and_low_level():
    kwargs = chart()
    settings = {"cash": 30_000}
    result = runtime.run(namespace(), settings=settings, **kwargs)
    settings["cash"] = 1
    snapshot = result.attrs["backtest_snapshot"]
    assert snapshot["settings"]["cash"] == 30_000
    assert snapshot["settings"]["commission_value"] == 0.2
    assert json.loads(json.dumps(snapshot, allow_nan=False)) == snapshot
    assert result["_strategy"].initial_timeframe == Timeframe.days(1)
    baseline = Backtest(
        kwargs["data"],
        Declared,
        cash=30_000,
        commission=0.002,
        context=kwargs["context"],
        instrument=kwargs["instrument"],
    ).run()
    pd.testing.assert_frame_equal(result["_trades"], baseline["_trades"])
    assert result["Equity Final [$]"] == baseline["Equity Final [$]"]
    assert result.attrs["plotting_result"] == baseline.attrs["plotting_result"]
    defaults = runtime.run(namespace(), **kwargs)
    assert defaults.attrs["backtest_snapshot"]["settings"]["cash"] == 20_000
    assert defaults["_strategy"] is not result["_strategy"]
    direct = Backtest(GOOG.iloc[:12], Declared).run()
    assert direct["_strategy"].timeframe is None
    assert direct["_equity_curve"]["Equity"].iloc[0] == 10_000


def test_context_conversion_and_no_resampling():
    args = chart(
        context=DataContext(Timeframe.minutes(15), "Asia/Shanghai"),
        instrument=InstrumentSpec(symbol="OTHER"),
    )
    original = args["data"].copy(deep=True)
    result = runtime.run(namespace(), options={"plotting_limits": None}, **args)
    strategy = result["_strategy"]
    assert str(strategy.data_index.tz) == "Asia/Shanghai"
    assert strategy.data_index.tz_convert("UTC").equals(original.index)
    assert strategy.timeframe == Timeframe.minutes(15)
    assert result.attrs["backtest_snapshot"]["instrument"]["symbol"] == "OTHER"
    pd.testing.assert_frame_equal(args["data"], original)


@pytest.mark.parametrize("zone", ["Asia/Shanghai", "America/New_York", "Asia/Kathmandu"])
@pytest.mark.parametrize("source_zone", ["UTC", "America/New_York"])
@pytest.mark.parametrize(
    "times,timeframe",
    [
        (["2026-01-05T01:00Z", "2026-01-05T02:00Z"], Timeframe.hours(1)),
        (["2026-03-08T06:30Z", "2026-03-08T07:30Z"], Timeframe.hours(1)),
        (["2026-11-01T05:30Z", "2026-11-01T06:30Z"], Timeframe.hours(1)),
        (["2024-02-28T20:00Z", "2024-02-29T20:00Z", "2024-03-01T20:00Z"], Timeframe.days(1)),
        (["2026-01-26T00:00Z", "2026-02-02T00:00Z"], Timeframe.weeks(1)),
        (["2024-01-31T23:00Z", "2024-02-29T23:00Z", "2024-03-31T23:00Z"], Timeframe.months(1)),
    ],
)
def test_chart_timezone_applies_before_strategy_and_preserves_bars(
    times, timeframe, source_zone, zone
):
    data = pd.DataFrame(
        {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 10.0},
        index=pd.to_datetime(times, utc=True).tz_convert(source_zone),
    )
    original = data.copy(deep=True)
    expected = data.index.tz_convert(zone)
    stages = []

    @backtest()
    class Observe(Strategy):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            check(self, expected)
            stages.append("construct")

        def init(self):
            check(self, expected)
            stages.append("init")

        def next(self):
            check(self, expected[: self.bar_index + 1])
            stages.append("next")

    def check(strategy, visible):
        for index in (strategy.data_index, strategy.data.index, strategy.df.index):
            assert index.equals(visible)
        assert strategy.timeframe == timeframe

    result = runtime.run(
        namespace(Observe),
        data=data,
        context=DataContext(timeframe, zone),
        instrument=InstrumentSpec(),
    )
    assert stages == ["construct", "init", *["next"] * len(data)]
    assert result["_equity_curve"].index.tz_convert(source_zone).equals(original.index)
    pd.testing.assert_frame_equal(data, original)


@pytest.mark.parametrize(
    "overrides",
    [
        {"context": None},
        {"instrument": None},
        {"options": []},
        {"options": {"unknown": 1}},
        {"options": {"plotting": 1}},
        {"options": {"plotting_limits": {}}},
        {"options": {"indicator_cache_bytes": -1}},
        {"context": "UTC"},
        {"data": GOOG.iloc[:12]},
        {"data": GOOG.iloc[:12].reset_index(drop=True)},
    ],
)
def test_runtime_invalid_context_and_options(overrides):
    with pytest.raises((TypeError, ValueError)):
        runtime.run(namespace(), **(chart() | overrides))


def test_low_level_invalid_context():
    with pytest.raises(TypeError, match="context"):
        Backtest(GOOG, Plain, context="bad")
    with pytest.raises(ValueError, match="带时区"):
        Backtest(GOOG, Plain, context=DataContext(Timeframe.days(1), "UTC"))


@pytest.mark.parametrize("kind", ["class", "params", "input", "set", "delete"])
def test_timeframe_reserved(kind):
    if kind in ("class", "input"):
        member = 2 if kind == "class" else inputs.int(2, title="周期")

        class Invalid(Plain):
            timeframe = member

        with pytest.raises((AttributeError, inputs.InputError), match="timeframe"):
            Backtest(GOOG.iloc[:12], Invalid).run()
    elif kind == "params":
        with pytest.raises(AttributeError, match="timeframe"):
            Backtest(GOOG.iloc[:12], Plain).run(timeframe=2)
    else:
        strategy = Backtest(GOOG.iloc[:12], Plain).run()["_strategy"]
        with pytest.raises(AttributeError, match="timeframe"):
            if kind == "set":
                strategy.timeframe = Timeframe.days(1)
            else:
                del strategy.timeframe


@pytest.mark.parametrize("mode", ["thread", "spawn"])
def test_context_survives_real_optimization(mode):
    import subprocess
    import sys
    from pathlib import Path

    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("context_spawn_probe.py")), mode],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout.splitlines()[-1]) == {
        "mode": mode,
        "contexts": 2,
        "timezone_cases": 6,
        "children": 0,
    }
    assert "resource_tracker" not in result.stderr


def test_parallel_runtime_context_isolation():
    from concurrent.futures import ThreadPoolExecutor

    def execute(case):
        minutes, zone = case
        result = runtime.run(
            namespace(),
            **chart(
                context=DataContext(Timeframe.minutes(minutes), zone),
                instrument=InstrumentSpec(symbol=str(minutes)),
            ),
        )
        return (
            result["_strategy"].timeframe,
            result.attrs["backtest_snapshot"],
            result["_equity_curve"].index,
        )

    cases = [(15, "Asia/Shanghai"), (60, "America/New_York")]
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(execute, cases))
    for (minutes, zone), (timeframe, snapshot, index) in zip(cases, results):
        assert timeframe == Timeframe.minutes(minutes)
        assert snapshot["instrument"]["symbol"] == str(minutes)
        assert snapshot["context"]["timezone"] == zone
        assert index.equals(chart()["data"].index.tz_convert(zone))
    assert declaration(Declared).cash == 20_000


@pytest.mark.parametrize("stage", ["init", "next"])
def test_runtime_propagates_strategy_failure_and_releases_session(stage):
    error = RuntimeError("strategy failed")

    @backtest()
    class Broken(Plain):
        pass

    def fail(self):
        raise error

    setattr(Broken, stage, fail)
    with pytest.raises(RuntimeError) as raised:
        runtime.run(namespace(Broken), **chart())
    assert raised.value is error
    # 上一次生命周期失败不污染后续声明及会话。
    assert runtime.run(namespace(), **chart())["_strategy"].initial_timeframe == Timeframe.days(1)


def test_runtime_complete_settings_and_snapshot_copies():
    @backtest(
        cash=25_000,
        margin=0.5,
        spread=0.001,
        commission_type=CommissionType.CASH_PER_ORDER,
        commission_value=1,
        execution_timing=ExecutionTiming.SAME_CLOSE,
        slippage_type=SlippageType.BPS,
        slippage_value=2,
        allow_short=False,
        max_gross_exposure=2,
        hedging=True,
        exclusive_orders=True,
        end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE,
    )
    class Configured(Plain):
        pass

    options = {"plotting": False, "indicator_cache_bytes": 0}
    result = runtime.run(namespace(Configured), options=options, **chart())
    snapshot = result.attrs["backtest_snapshot"]
    assert snapshot["settings"] == declaration(Configured).snapshot()
    assert snapshot["settings"]["slippage_type"] == "bps"
    assert snapshot["settings"]["slippage_value"] == 2.0
    assert snapshot["settings"]["commission_type"] == "cash_per_order"
    assert snapshot["settings"]["commission_value"] == 1.0
    assert snapshot["schemaVersion"] == 2
    assert snapshot["options"]["indicator_cache_bytes"] == 0
    options["plotting"] = True
    assert snapshot["options"]["plotting"] is False
    assert json.loads(json.dumps(snapshot, allow_nan=False)) == snapshot
    descriptor = runtime.describe(namespace(Configured))
    assert descriptor["backtest"]["schemaVersion"] == 2
    descriptor["backtest"]["settings"]["slippage_value"] = 100
    assert declaration(Configured).slippage_value == 2

    @backtest()
    class Redeclared(Configured):
        pass

    assert declaration(Redeclared) == BacktestSettings()
    assert runtime.describe(namespace(Redeclared))["backtest"]["settings"]["cash"] == 10_000


def test_context_retains_prices_gaps_and_data_validation():
    args = chart()
    # 本地休市缺口保留，周期来自图表元信息，不从观测间隔猜测。
    args["data"] = args["data"].iloc[[0, 1, 5, 8, 11]]
    result = runtime.run(namespace(), **args)
    pd.testing.assert_frame_equal(result["_strategy"].df, args["data"])
    assert result["_strategy"].timeframe == Timeframe.days(1)
    args["data"].iloc[0, args["data"].columns.get_loc("Close")] = -1
    with pytest.raises(ValueError, match="OHLC"):
        runtime.run(namespace(), **args)
