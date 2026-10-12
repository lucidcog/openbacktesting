"""方法式入口与独立计算共享计算契约；具名结果仅持有当前运行视图。"""

import inspect
import pickle
from multiprocessing.pool import ThreadPool

import openbacktesting as api
import numpy as np
import pandas as pd
import pytest
from openbacktesting import inputs
from openbacktesting.data import _Data
from openbacktesting.indicator_api import IndicatorResult
from openbacktesting.indicator_methods import TechnicalAnalysis
from openbacktesting.indicator_types import IndicatorError, IndicatorHandle
from openbacktesting.indicators import runtime as indicators
from test_indicator_catalog import AVAILABLE, catalog_data


class Empty(api.Strategy):
    def init(self):
        pass

    def next(self):
        pass


def strategy(data=None):
    data = _Data(catalog_data() if data is None else data)
    data._indicator_cache = indicators.IndicatorCache()
    return Empty(None, data, {})


@pytest.mark.parametrize("spec", AVAILABLE, ids=lambda spec: spec.id)
def test_every_method_signature_values_metadata_and_properties(spec):
    owner = strategy()
    method = getattr(owner.ta, spec.id.removeprefix("ta."))
    signature = inspect.signature(method)
    assert spec.id in method.__doc__
    for name, rule in spec.parameters:
        assert signature.parameters[name].default == rule.default
        assert signature.parameters[name].kind == inspect.Parameter.KEYWORD_ONLY
    fluent = method()
    direct = indicators.compute(
        spec.id,
        owner.data.df,
        cache=owner._data._indicator_cache,
        cursor=owner._indicator_cursor,
    )
    assert len(owner._indicators) == 1
    assert owner._data._indicator_cache.hits == 1
    if len(spec.outputs) == 1:
        assert isinstance(fluent, IndicatorHandle)
        np.testing.assert_array_equal(fluent, direct)
    else:
        assert isinstance(fluent, IndicatorResult)
        pd.testing.assert_frame_equal(fluent.df, direct.df)
        for name in spec.outputs:
            channel = getattr(fluent, name)
            assert channel is getattr(fluent, name) is fluent[name]
            assert channel._values is direct._values
            assert channel._valid is direct._valid
            assert channel._cursor is owner._indicator_cursor
            np.testing.assert_array_equal(channel, direct[name])
            with pytest.raises(AttributeError):
                setattr(fluent, name, None)
        with pytest.raises(AttributeError):
            _ = fluent.nonexistent
        with pytest.raises(KeyError):
            fluent["nonexistent"]
        with pytest.raises(KeyError):
            fluent[0]
        with pytest.raises(TypeError):
            fluent + 1
    np.testing.assert_array_equal(fluent.valid, direct.valid)
    np.testing.assert_array_equal(fluent.ready, direct.ready)
    assert fluent.metadata == direct.metadata
    for bar in (200, 333):
        owner._indicator_cursor.length = bar
        if isinstance(fluent, IndicatorResult):
            for name in spec.outputs:
                assert len(getattr(fluent, name)) == bar
                np.testing.assert_array_equal(getattr(fluent, name), direct[name])
        else:
            assert len(fluent) == bar


@pytest.mark.parametrize(
    "cls",
    [
        api.Strategy,
        api.engine.Strategy,
        api.lib.Strategy,
        api.lib.SignalStrategy,
        api.lib.TrailingStrategy,
    ],
)
def test_strategy_has_no_public_dynamic_indicator_entry(cls):
    assert not hasattr(cls, "indicator")
    owner = strategy()
    with pytest.raises(AttributeError, match="indicator"):
        _ = owner.indicator
    assert isinstance(owner.ta.ema(length=20), IndicatorHandle)
    assert isinstance(owner.ind(lambda: np.ones(len(owner.data))), IndicatorHandle)


def test_method_inventory_and_namespace_access_do_not_compute():
    owner = strategy()
    assert owner.ta is owner.ta
    assert not owner._indicators
    methods = {name for name, member in vars(TechnicalAnalysis).items() if callable(member)}
    assert methods == {spec.id.removeprefix("ta.") for spec in AVAILABLE}
    for spec in indicators.catalog():
        if spec.status != "available":
            with pytest.raises(AttributeError):
                getattr(owner.ta, spec.id.removeprefix("ta."))


def test_sources_options_and_default_normalization():
    owner = strategy()
    assert owner.ta.ema().metadata == owner.ta.ema(None, length=10).metadata
    ema = owner.ta.ema("Open", length=7)
    direct = owner.ta.ema(inputs={"close": "Open"}, length=7)
    np.testing.assert_array_equal(ema, direct)
    macd = owner.ta.macd(required_outputs=["histogram"])
    assert macd.line is macd.macd
    smooth = owner.ta.ema(macd.histogram, length=5)
    same = owner.ta.ema(inputs={"close": macd.histogram}, length=5)
    assert smooth.metadata == same.metadata
    assert smooth.metadata["inputs"]["close"]["channel"] == "histogram"
    np.testing.assert_array_equal(smooth, same)
    sma = owner.ta.sma(inputs={"close": "Open"}, backend="pandas.sma", length=2)
    assert sma.metadata["backend"] == "pandas.sma"
    atr = owner.ta.atr(inputs={"close": "Open"})
    assert atr.metadata["inputs"] == {"close": "Open"}
    assert "warmup" not in owner.ta.ema(required_outputs=[]).metadata
    assert owner.ta.ema(inputs={}).shape == (512,)
    snapshot = macd.df
    snapshot.iloc[:] = 0
    assert not (macd.df.iloc[-1] == 0).all()
    metadata = macd.metadata
    metadata["parameters"]["fast"] = 200
    assert macd.metadata["parameters"]["fast"] == 12
    before = len(owner._indicators)
    for _ in range(30):
        assert macd.histogram is macd["histogram"]
    assert len(owner._indicators) == before


@pytest.mark.parametrize(
    "call, error",
    [
        (lambda s: s.ta.ema(20), "missing-input"),
        (lambda s: s.ta.ema(s.ta.macd()), "选择通道"),
        (lambda s: s.ta.ema(np.ones(512)), "missing-input"),
        (lambda s: s.ta.ema("Close", inputs={}), "invalid-parameter"),
        (lambda s: s.ta.ema(strategy().ta.ema()), "index-mismatch"),
        (lambda s: s.ta.ema(length=0), "invalid-parameter"),
        (lambda s: s.ta.ema(length=True), "invalid-parameter"),
        (lambda s: s.ta.ema(backend="nope"), "backend-unavailable"),
        (lambda s: s.ta.macd(required_outputs=["line"]), "output-contract"),
    ],
)
def test_invalid_values_fail_without_bad_registration(call, error):
    owner = strategy()
    with pytest.raises(IndicatorError, match=error):
        call(owner)
    # 唯一可能成功的预备登记是生成被拒绝的整个 MACD 结果。
    assert all(h.metadata["id"] == "ta.macd" for h in owner._indicators)


def test_signature_rejection_missing_fields_and_stage_errors():
    owner = strategy()
    for call in (
        lambda: owner.ta.ema(talib=True),
        lambda: owner.ta.ema("Close", 3),
        lambda: owner.ta.atr("Close"),
    ):
        with pytest.raises(TypeError):
            call()
    missing = strategy(catalog_data().drop(columns=["benchmark"]))
    with pytest.raises(IndicatorError, match="missing-input"):
        missing.ta.beta()
    assert not missing._indicators
    owner._indicator_cursor.phase = "next"
    with pytest.raises(IndicatorError, match="invalid-phase"):
        owner.ta.ema()
    assert not owner._indicators


@pytest.mark.parametrize("value", [3, lambda self: None, inputs.int(10, title="period")])
def test_reserved_ta_class_and_inherited_fields(value):
    parent = type("Conflict", (Empty,), {"ta": value})
    child = type("Inherited", (parent,), {})
    for cls in (parent, child):
        with pytest.raises(AttributeError, match="保留属性.*改名"):
            cls(None, _Data(catalog_data()), {})


def test_reserved_assignment_parameters_and_unrelated_input_title():
    owner = strategy()
    with pytest.raises(AttributeError, match="保留属性"):
        owner.ta = 10
    with pytest.raises(AttributeError, match="保留属性"):
        Empty(None, _Data(catalog_data()), {"ta": 1})

    class InputTitle(Empty):
        length = inputs.int(10, title="ta")

        def init(self):
            self.average = self.ta.ema(length=self.length)

    result = api.Backtest(catalog_data(), InputTitle).run()
    assert result["_strategy"].average.metadata["parameters"]["length"] == 10


class Trading(api.Strategy):
    named_access = True
    length = 10

    def init(self):
        if self.named_access:
            self.average = self.ta.ema(length=self.length)
            self.momentum = self.ta.macd()
            self.histogram = self.momentum.histogram
        else:
            self.average = self.ta.ema(length=self.length)
            self.momentum = self.ta.macd()
            self.histogram = self.momentum["histogram"]
        self.visited = []

    def next(self):
        self.visited.append(len(self.data))
        assert len(self.histogram) == len(self.data)
        if self.histogram[-1] > 0 and not self.position:
            self.buy(qty=1)
        elif self.histogram[-1] < 0 and self.position:
            self.position.close()


def test_trade_equivalence_repeated_run_and_pickle():
    bt = api.Backtest(catalog_data(), Trading, end_policy="close_at_last_close")
    old = bt.run(named_access=False)
    new = bt.run()
    repeated = bt.run()
    for result in (new, repeated):
        pd.testing.assert_frame_equal(old["_trades"], result["_trades"])
        pd.testing.assert_frame_equal(old["_equity_curve"], result["_equity_curve"])
        pd.testing.assert_series_equal(old.filter(regex="^[^_]"), result.filter(regex="^[^_]"))
        assert result.attrs == old.attrs
        assert old["_strategy"].visited == result["_strategy"].visited
    first, second = new["_strategy"], repeated["_strategy"]
    assert first.ta is not second.ta
    assert first._indicator_cursor is not second._indicator_cursor
    restored = pickle.loads(pickle.dumps(first))
    assert restored.ta._register.__self__ is restored
    assert restored.momentum.histogram is restored.histogram
    assert restored.momentum.line is restored.momentum.macd
    np.testing.assert_array_equal(restored.histogram, first.histogram)
    assert restored.histogram._cursor is restored._indicator_cursor
    with pytest.raises(ValueError):
        restored.histogram._values.setflags(write=True)
    with pytest.raises(IndicatorError, match="invalid-phase"):
        restored.ta.ema()


@pytest.mark.parametrize("budget", [0, indicators.DEFAULT_CACHE_BYTES])
def test_cache_counts_and_failed_backend_retry(monkeypatch, budget):
    owner = strategy()
    owner._data._indicator_cache = indicators.IndicatorCache(budget)
    calls = []
    original = indicators.execute

    def execute(*args):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("backend failed")
        return original(*args)

    monkeypatch.setattr(indicators, "execute", execute)
    with pytest.raises(IndicatorError, match="calculation-failed"):
        owner.ta.macd()
    assert not owner._indicators
    result = owner.ta.macd()
    owner.ta.macd()
    assert len(calls) == (2 if budget else 3)
    assert len(owner._indicators) == 2
    assert result.histogram is result.histogram


def test_thread_optimization_equivalence_and_scope(monkeypatch):
    monkeypatch.setattr(api, "Pool", lambda: ThreadPool(2))
    bt = api.Backtest(catalog_data(150), Trading, end_policy="close_at_last_close")
    old, oh = bt.optimize(length=[5, 10], named_access=[False], return_heatmap=True)
    new, nh = bt.optimize(length=[5, 10], named_access=[True], return_heatmap=True)
    np.testing.assert_array_equal(oh, nh)
    pd.testing.assert_frame_equal(old["_trades"], new["_trades"])
    assert not indicators._OPTIMIZATION_CACHES
    assert new["_strategy"].ta._register.__self__ is new["_strategy"]


def test_real_spawn_equivalence():
    import json
    import subprocess
    import sys
    from pathlib import Path

    process = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("fluent_spawn_probe.py"))],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert json.loads(process.stdout.splitlines()[-1]) == {"equivalent": True, "active_children": 0}
    assert "resource_tracker" not in process.stderr


def test_compute_custom_and_named_output_consumption():
    owner = strategy()
    direct = owner.ta.macd()
    pure = indicators.compute("ta.macd", catalog_data())
    custom = owner.ind(lambda: np.arange(512, dtype=float))
    assert isinstance(direct, IndicatorResult)
    assert isinstance(pure, IndicatorHandle)
    np.testing.assert_array_equal(direct.macd, pure["macd"])
    assert custom[-1] == 511


@pytest.mark.parametrize("use_source", [True, False])
def test_all_nan_and_mid_history_gaps_keep_broker_running(use_source):
    visits = []

    class Gaps(api.Strategy):
        def init(self):
            self.line = (
                self.ta.sma("source", length=2)
                if use_source
                else self.ta.sma(inputs={"close": "source"}, length=2)
            )

        def next(self):
            visits.append(len(self.data) - 1)
            if len(visits) == 1:
                self.buy(qty=1, sl=self.data.Close[-1] - 1)

    data = catalog_data(50)
    data.loc[:, ["Open", "Close"]] = 100.0
    data.loc[:, "High"] = 101.0
    data.loc[:, "Low"] = 100.0
    data.loc[:, "source"] = 100.0
    data.iloc[12, data.columns.get_loc("Low")] = 98.0
    data.iloc[12:15, data.columns.get_loc("source")] = np.nan
    result = api.Backtest(data, Gaps, end_policy="close_at_last_close").run()
    assert visits == list(range(50))
    assert result["_trades"].iloc[0].ExitBar == 12
    assert result["_trades"].iloc[0].ExitPrice == 99
    visits.clear()
    data.loc[:, "source"] = np.nan
    result = api.Backtest(data, Gaps).run()
    assert visits == list(range(50))
    assert len(result["_strategy"].line) == len(data)


@pytest.mark.parametrize("phase", ["init", "next"])
def test_fluent_failed_run_restores_full_diagnostics(phase):
    captured = []

    class Failed(Empty):
        def init(self):
            self.result = self.ta.macd()
            captured.append(self)
            if phase == "init":
                raise RuntimeError("failed init")

        def next(self):
            raise RuntimeError("failed next")

    with pytest.raises(RuntimeError, match="failed " + phase):
        api.Backtest(catalog_data(100), Failed).run()
    owner = captured[0]
    assert len(owner.result.histogram) == 100
    assert owner._data._indicator_cache is None
    with pytest.raises(IndicatorError, match="invalid-phase"):
        owner.ta.ema()
