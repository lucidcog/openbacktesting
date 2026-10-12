"""Numerical, index, readiness, backend, and isolation contracts for owned indicators."""

import builtins
import pickle
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import numpy as np
import pandas as pd
import pytest
from test_indicator_regressions import frame

from openbacktesting import Backtest, Strategy
from openbacktesting.indicator_types import (
    IndicatorCursor,
    IndicatorError,
    IndicatorHandle,
    IndicatorSpec,
    Parameter,
    immutable,
)
from openbacktesting.indicators import runtime as indicators


@pytest.mark.parametrize("name", ["sma", "ema", "rsi", "atr", "macd", "bbands"])
def test_representative_native_contract_and_causality(name, monkeypatch):
    import pandas_ta_classic as ta

    original = builtins.__import__

    def reject_talib(module, *args, **kwargs):
        if module == "talib":
            raise AssertionError("Built-in indicators must not import TA-Lib")
        return original(module, *args, **kwargs)

    monkeypatch.setitem(ta.Imports, "talib", True)
    monkeypatch.setattr(builtins, "__import__", reject_talib)
    data = frame(100)
    result = indicators.compute(f"ta.{name}", data)
    assert result.shape[-1] == 100
    assert result.s.index.equals(data.index)
    for n in [40, 67]:
        prefix = indicators.compute(f"ta.{name}", data.iloc[:n])
        np.testing.assert_allclose(np.asarray(result)[..., :n], np.asarray(prefix), equal_nan=True)
        np.testing.assert_array_equal(result.valid[..., :n], prefix.valid)
    restored = pickle.loads(pickle.dumps(result))
    np.testing.assert_allclose(restored, result, equal_nan=True)
    with pytest.raises(ValueError):
        np.asarray(result).setflags(write=True)


def test_sma_backends_and_hand_calculated_ema():
    data = frame()
    for backend in [None, "pandas.sma"]:
        actual = indicators.compute("ta.sma", data, parameters={"length": 3}, backend=backend)
        np.testing.assert_allclose(actual, [np.nan, np.nan, *range(101, 109)])
    ema = indicators.compute("ta.ema", data, parameters={"length": 3})
    np.testing.assert_allclose(ema, [np.nan, np.nan, *range(101, 109)])
    assert ema.first_ready() == 2
    assert indicators.describe("ta.sma").id == "ta.sma"
    assert len(indicators.catalog()) >= 6


@pytest.mark.parametrize(
    "parameters", [{"length": 0}, {"length": True}, {"length": 2.5}, {"unknown": 1}]
)
def test_parameter_errors_precede_computation(parameters, monkeypatch):
    monkeypatch.setattr(indicators, "execute", lambda *a: pytest.fail("Backend must not be called"))
    with pytest.raises(IndicatorError, match="invalid-parameter"):
        indicators.compute("ta.sma", frame(), parameters=parameters)


def test_backend_and_input_errors():
    for backend in ["talib", "unknown", "pandas.sma"]:
        with pytest.raises(IndicatorError, match="backend-unavailable"):
            indicators.compute("ta.ema", frame(), backend=backend)
    with pytest.raises(IndicatorError, match="unknown-indicator"):
        indicators.describe("unknown")
    for data in [None, frame().set_axis([0] * 10)]:
        with pytest.raises(IndicatorError, match="index-mismatch"):
            indicators.compute("ta.sma", data)
    for mapping in [{"other": "Close"}, {"close": "absent"}, {"close": 1}]:
        with pytest.raises(IndicatorError, match="missing-input"):
            indicators.compute("ta.sma", frame(), inputs=mapping)
    with pytest.raises(IndicatorError, match="missing-input"):
        indicators.compute("ta.sma", frame().assign(Close="a"))
    with pytest.raises(IndicatorError, match="output-contract"):
        indicators.compute("ta.sma", frame(), required_outputs=["absent"])


def test_short_history_and_backend_failures(monkeypatch):
    result = indicators.compute("ta.sma", frame(3))
    assert np.isnan(result).all()
    assert result.first_ready() == 3
    for bad, code in [
        (None, "output-contract"),
        ([1], "output-contract"),
        (pd.Series(np.ones(10), name="sma"), "index-mismatch"),
        (pd.DataFrame(np.ones((10, 2)), index=frame().index), "output-contract"),
    ]:
        monkeypatch.setattr(indicators, "execute", lambda *args, bad=bad: bad)
        with pytest.raises(IndicatorError, match=code):
            indicators.compute("ta.sma", frame())

    def broken(*args):
        raise RuntimeError("source failed")

    monkeypatch.setattr(indicators, "execute", broken)
    with pytest.raises(IndicatorError) as info:
        indicators.compute("ta.sma", frame())
    assert isinstance(info.value.__cause__, RuntimeError)


def test_handle_views_scalars_conversion_and_write_protection():
    cursor = IndicatorCursor(5)
    handle = IndicatorHandle(
        np.arange(10.0).reshape(2, 5), name=("a", "b"), index=pd.RangeIndex(5), cursor=cursor
    )
    a, b = handle
    tail = b[-2:]
    cursor.length = 3
    assert handle.shape == (2, 3)
    assert a[-1] == 2 and b[-1] == 7
    np.testing.assert_array_equal(tail, [6, 7])
    assert tail.s.index.tolist() == [1, 2]
    assert handle.df.columns.tolist() == ["a", "b"]
    assert float(b) == 7 and bool(b)
    assert b.dtype == np.dtype(float)
    np.testing.assert_array_equal(handle["a"], [0, 1, 2])
    with pytest.raises(KeyError):
        handle["absent"]
    with pytest.raises(IndexError):
        b[3]
    with pytest.raises(ValueError, match="copy=False"):
        np.asarray(b, copy=False)
    with pytest.raises(TypeError):
        np.add(b, 1, out=b)
    with pytest.raises(TypeError):
        np.add.at(b, 0, 1)
    np.testing.assert_array_equal(b + 1, [6, 7, 8])
    np.testing.assert_array_equal(b.astype(int), [5, 6, 7])
    copied = b.copy()
    copied[0] = 999
    series_copy = b.s
    series_copy.iloc[0] = 999
    assert b[0] == 5
    assert handle.valid.shape == (2, 3)
    assert b.valid.tolist() == [True] * 3
    single = IndicatorHandle([0.0, 1.0], name="one", index=pd.RangeIndex(2))
    assert single["one"].df.columns.tolist() == ["one"]
    assert single.ready_at(0)
    with pytest.raises(ValueError):
        immutable([object()])


@pytest.mark.parametrize(
    "rule,value",
    [
        (Parameter(0.5, "float", minimum=0, maximum=1), 2),
        (Parameter(0.5, "float"), float("nan")),
        (Parameter("a", "str", choices=("a", "b")), "c"),
        (Parameter(True, "bool"), 1),
    ],
)
def test_parameter_constraints(rule, value):
    with pytest.raises(IndicatorError):
        rule.normalize(value, "test", "param")


def test_definitions_and_parameter_relations():
    for kwargs in [
        {"id": "", "outputs": ("a",)},
        {"id": "x", "outputs": ()},
        {"id": "x", "outputs": ("a", "a")},
        {"id": "x", "outputs": ("a",), "required": ("b",)},
        {"id": "x", "outputs": ("a",), "parameters": (("inputs", Parameter(1, "int")),)},
    ]:
        with pytest.raises(ValueError):
            IndicatorSpec(source="test", category="test", inputs=(), **kwargs)
    for name, params in [("macd", {"fast": 30}), ("bbands", {"ddof": 5})]:
        with pytest.raises(IndicatorError):
            indicators.compute(f"ta.{name}", frame(100), parameters=params)
    assert Parameter(0.5, "float", minimum=0, maximum=1).normalize(0.5, "x", "p") == 0.5
    h = IndicatorHandle([np.nan], name="x", index=pd.RangeIndex(1))
    assert h.first_ready() == 1 and not h.ready_at(0)


def test_cache_equivalence_budget_eviction_and_data_invalidation():
    cache = indicators.IndicatorCache(1000)
    data = frame(20)
    a = indicators.compute("ta.sma", data, cache=cache)
    b = indicators.compute("ta.sma", data, parameters={"length": 10}, cache=cache)
    assert cache.hits == 1 and a is not b
    a.metadata["parameters"]["length"] = 1000
    assert b.metadata["parameters"]["length"] == 10
    data.loc[data.index[-1], "Close"] = 999
    c = indicators.compute("ta.sma", data, cache=cache)
    assert c[-1] != b[-1]
    for length in range(2, 9):
        indicators.compute("ta.sma", data, parameters={"length": length}, cache=cache)
        assert cache.bytes <= cache.budget
    np.testing.assert_allclose(a, b, equal_nan=True)
    cache.clear()
    assert cache.bytes == 0
    for budget in [0, 1]:
        tiny = indicators.IndicatorCache(budget)
        indicators.compute("ta.sma", data, cache=tiny)
        assert tiny.bytes == 0
    for bad in [-1, True, 1.5]:
        with pytest.raises(ValueError):
            indicators.IndicatorCache(bad)


def test_cache_single_flight_and_retry():
    cache = indicators.IndicatorCache()
    entered, finish = Event(), Event()
    calls = []

    def calculate():
        calls.append(1)
        entered.set()
        assert finish.wait(5)
        return IndicatorHandle([1], name="x", index=pd.RangeIndex(1))

    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(cache.get, "x", calculate)
        assert entered.wait(5)
        second = pool.submit(cache.get, "x", calculate)
        finish.set()
        assert first.result() is second.result()
    assert calls == [1]

    def broken():
        raise ValueError("failure")

    with pytest.raises(ValueError):
        cache.get("bad", broken)
    assert cache.get("bad", calculate)[-1] == 1


def test_strategy_registration_composition_and_midstream_gap():
    seen = []

    class Probe(Strategy):
        def init(self):
            self.sma = self.ta.sma(length=2)
            self.double = self.ta.sma(length=2, inputs={"close": self.sma})
            values = np.ones(10)
            values[4] = np.nan
            self.event = self.ind(lambda: values)

        def next(self):
            seen.append(len(self.data) - 1)
            with pytest.raises(IndicatorError, match="invalid-phase"):
                self.ta.sma()
            with pytest.raises(IndicatorError, match="invalid-phase"):
                self.ind(lambda: np.ones(10))

    stats = Backtest(frame(), Probe).run()
    assert seen == list(range(10))
    assert len(stats.attrs["indicator_snapshot"]["indicators"]) == 3
    source = indicators.compute("ta.sma", frame())
    with pytest.raises(IndicatorError, match="index-mismatch"):
        indicators.compute("ta.sma", frame(), inputs={"close": source})


def test_optional_channels_context_alignment_and_legacy_warmup():
    from types import SimpleNamespace

    from openbacktesting.data import _Indicator, _indicator_warmup_nbars

    data = frame(5)
    optional = indicators.compute("ta.sma", data, required_outputs=[])
    assert optional.first_ready() == 5 and not optional.ready_at(0)
    assert not optional.valid.any()
    assert optional.metadata["required_outputs"] == [] and "warmup" not in optional.metadata
    cursor = IndicatorCursor(5)
    source = IndicatorHandle(np.ones(5), name="x", index=data.index, cursor=cursor)
    with pytest.raises(IndicatorError, match="index-mismatch"):
        indicators.compute("ta.sma", data, cursor=cursor, inputs={"close": source[1:]})
    legacy = _Indicator([np.nan, 1.0, 2.0], name="old")
    assert _indicator_warmup_nbars(SimpleNamespace(x=legacy)) == 1


def test_parameter_relations_and_duplicate_catalog(monkeypatch):
    import importlib.resources
    import json
    from types import SimpleNamespace

    from openbacktesting.indicators import common as indicator_backends

    for name, params in [
        ("mavp", {"minperiod": 30}),
        ("mama", {"slowlimit": 0.5}),
        ("squeeze_pro", {"kc_scalar_wide": 1}),
    ]:
        with pytest.raises(IndicatorError, match="invalid-parameter"):
            indicators.describe("ta." + name).normalize(params)
    source = (
        importlib.resources.files("openbacktesting.indicators")
        .joinpath("catalog.json")
        .read_text()
    )
    rows = json.loads(source)
    rows["entries"].append(rows["entries"][0])
    fake = SimpleNamespace(joinpath=lambda _: SimpleNamespace(read_text=lambda: json.dumps(rows)))
    monkeypatch.setattr(importlib.resources, "files", lambda _: fake)
    with pytest.raises(ValueError, match="Duplicate indicator identity"):
        indicator_backends.load_specs()


def test_private_pattern_fixture_preserves_score_validity_and_confirmation(monkeypatch):
    spec = IndicatorSpec(
        "candle.fixture",
        "fixture",
        "candles",
        ("close",),
        ("score",),
        minimum=3,
        dtype="int64",
        unit="signed-score",
    )
    monkeypatch.setitem(indicators._CATALOG, spec.id, spec)
    from openbacktesting.indicators.registry import BINDINGS, NATIVE, Binding

    monkeypatch.setitem(BINDINGS, (spec.id, NATIVE), Binding(lambda: None, "fixture-1"))
    monkeypatch.setattr(
        indicators,
        "execute",
        lambda spec, values, params, backend: pd.Series(
            [0, 0, 0, 100, -100], index=values["close"].index, name="score"
        ),
    )
    cache = indicators.IndicatorCache()
    result = indicators.compute(spec.id, frame(5), cache=cache)
    assert result.dtype == np.dtype("int64")
    assert result.first_ready() == 2
    assert result.valid.tolist() == [False, False, True, True, True]
    assert result.ready.tolist() == [False, False, True, True, True]
    assert result[2] == 0 and result[3] == 100 and result[4] == -100
    assert result.metadata["unit"] == "signed-score"
    again = indicators.compute(spec.id, frame(5), cache=cache)
    assert cache.hits == 1
    np.testing.assert_array_equal(again, result)


def test_hand_calculated_rsi_atr_bbands_and_snapshot_isolation():
    data = frame(40)
    rsi = indicators.compute("ta.rsi", data, parameters={"length": 3})
    np.testing.assert_allclose(np.asarray(rsi)[3:], 100.0)
    atr = indicators.compute("ta.atr", data, parameters={"length": 3})
    np.testing.assert_allclose(np.asarray(atr)[3:], 1.0)
    bands = indicators.compute("ta.bbands", data, parameters={"length": 3})
    assert bands["middle"][2] == 101.0
    np.testing.assert_allclose(bands["upper"][2], 101 + 2 * np.sqrt(2 / 3))
    snapshot = bands.metadata
    snapshot["parameters"]["length"] = -1
    assert bands.metadata["parameters"]["length"] == 3
    cursor = IndicatorCursor(40)
    a = IndicatorHandle(np.ones(40), name="a", index=data.index, cursor=cursor)
    cursor.length = 5
    snapshot = np.asarray(a)
    cursor.length = 10
    assert len(snapshot) == 5 and len(a) == 10
    assert not snapshot.flags.writeable


def test_gap_preserves_strategy_callbacks_and_existing_stop_orders():
    calls = []

    class Stop(Strategy):
        def init(self):
            values = np.ones(len(self.data))
            values[4] = np.nan
            self.container = {"nested": [(self.ind(lambda: values),)]}

        def next(self):
            calls.append(len(self.data) - 1)
            assert len(self.container["nested"][0][0]) == len(self.data)
            if len(self.data) == 3:
                self.buy(qty=1, sl=100.0)

    data = frame(10)
    data.loc[data.index[4], "Low"] = 99.0
    stats = Backtest(data, Stop).run()
    assert calls == list(range(10))
    assert stats["_trades"].iloc[0].ExitBar == 4
    assert stats["_trades"].iloc[0].ExitPrice == 100.0


def test_input_adapter_materializes_once_and_cannot_mutate_source():
    data = frame()
    spec = indicators.describe("ta.sma")
    prepared = indicators._prepare_inputs(spec, data, None, None)
    assert not np.shares_memory(prepared.close.to_numpy(), data.Close.to_numpy())
    prepared.iloc[0, 0] = -999
    assert data.Close.iloc[0] == 100.0


def test_cache_versions_backend_and_data_index_are_part_of_identity(monkeypatch):
    from dataclasses import replace

    cache = indicators.IndicatorCache()
    data = frame(20)
    spec = indicators.describe("ta.sma")
    indicators.compute(spec.id, data, cache=cache)
    monkeypatch.setitem(indicators._CATALOG, spec.id, replace(spec, version="2"))
    indicators.compute(spec.id, data, cache=cache)
    indicators.compute(spec.id, data, backend="pandas.sma", cache=cache)
    indicators.compute(spec.id, data.set_axis(data.index.tz_localize("UTC")), cache=cache)
    assert cache.misses == 4 and cache.hits == 0


def test_user_example_exports_bt_and_retains_both_snapshots():
    import runpy
    from pathlib import Path

    from example_support import example_chart

    from openbacktesting import runtime

    namespace = runpy.run_path(str(Path(__file__).parents[1] / "examples/strategies/ema_macd.py"))
    assert "bt" not in namespace
    stats = runtime.run(namespace, **example_chart(namespace))
    assert "input_snapshot" in stats.attrs and "indicator_snapshot" in stats.attrs
    assert [item["id"] for item in stats.attrs["indicator_snapshot"]["indicators"]] == [
        "ta.ema",
        "ta.macd",
    ]


def test_cache_failure_wakes_concurrent_waiter_and_does_not_poison_retry(monkeypatch):
    from concurrent.futures import Future

    cache = indicators.IndicatorCache()
    entered, waiting, release = Event(), Event(), Event()
    original = Future.result

    def result(self, *args, **kwargs):
        waiting.set()
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Future, "result", result)

    def fail():
        entered.set()
        assert release.wait(5)
        raise RuntimeError("shared failure")

    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(cache.get, "key", fail)
        assert entered.wait(5)
        second = pool.submit(cache.get, "key", fail)
        assert waiting.wait(5)
        release.set()
        for pending in (first, second):
            with pytest.raises(RuntimeError, match="shared failure"):
                original(pending, timeout=5)
    value = cache.get("key", lambda: IndicatorHandle([1.0], name="x", index=pd.RangeIndex(1)))
    assert value[-1] == 1.0 and cache.misses == 2


def test_historical_result_table_remains_usable_by_statistics():
    from test_modularization import baseline_objects

    from openbacktesting.portfolio.stats import compute_stats
    from openbacktesting.test import GOOG

    old = baseline_objects()["result"]
    result = compute_stats(
        trades=old["_trades"],
        equity=old["_equity_curve"].Equity.to_numpy(),
        ohlc_data=GOOG.iloc[:80],
        strategy_instance=old["_strategy"],
    )
    # Historical serialized indicators remain consumable; override only explicitly changed statistics and retain historical baseline files.
    # Fixed equity is unchanged: annualization includes the initial zero-return bucket, buy-and-hold starts at bar 0, and Alpha adjusts accordingly.
    expected = old.copy()
    expected.update(
        pd.Series(
            {
                "Buy & Hold Return [%]": (GOOG.Close.iloc[79] / GOOG.Close.iloc[0] - 1) * 100,
                "Return (Ann.) [%]": 130.8690334993717,
                "Volatility (Ann.) [%]": 130.53767193686298,
                "Sharpe Ratio": 1.0025384362812062,
                "Sortino Ratio": 4.404054552002119,
                "Calmar Ratio": 4.593816316795483,
                "Alpha [%]": -5.591826602443781,
            }
        )
    )
    assert np.isnan(result["Exposure Time [%]"])
    pd.testing.assert_series_equal(
        result.filter(regex="^[^_]").drop("Exposure Time [%]"),
        expected.filter(regex="^[^_]").drop("Exposure Time [%]"),
        check_exact=False,
        rtol=1e-12,
        atol=1e-12,
    )
    for key in ("_trades", "_equity_curve"):
        pd.testing.assert_frame_equal(result[key], old[key], check_exact=True)


def test_non_numeric_backend_output_is_a_classified_error(monkeypatch):
    monkeypatch.setattr(
        indicators,
        "execute",
        lambda *args: pd.Series(["bad"] * 10, index=frame().index, name="sma"),
    )
    with pytest.raises(IndicatorError, match="output-contract") as info:
        indicators.compute("ta.sma", frame())
    assert isinstance(info.value.__cause__, ValueError)


def test_registered_index_is_detached_and_input_dtype_affects_cache():
    index_values = np.arange(20)
    index = pd.Index(index_values, copy=False)
    handle = IndicatorHandle(np.ones(20), name="x", index=index)
    original_index = handle.s.index.copy(deep=True)
    index_values[0] = 999
    assert handle.s.index.equals(original_index)
    data = frame(20)
    cache = indicators.IndicatorCache()
    a = indicators.compute("ta.sma", data, cache=cache)
    b = indicators.compute("ta.sma", data.astype(int), cache=cache)
    np.testing.assert_allclose(a, b, equal_nan=True)
    assert cache.hits == 0 and cache.misses == 2
    assert a.metadata["input_dtypes"] == {"close": "float64"}
    assert b.metadata["input_dtypes"] == {"close": "int64"}
    assert indicators.describe("ta.msw").history_sum == (("period", 1),)


def test_fifty_registered_indicators_compute_only_during_init(monkeypatch):
    calls = []
    original = indicators.execute

    def counted(*args):
        calls.append(args[2]["length"])
        return original(*args)

    monkeypatch.setattr(indicators, "execute", counted)
    seen = []

    class Fifty(Strategy):
        def init(self):
            self.lines = {length: self.ta.sma(length=length) for length in range(2, 52)}

        def next(self):
            assert len(calls) == 50
            assert all(len(line) == len(self.data) for line in self.lines.values())
            seen.append(sum(line[-1] for line in self.lines.values()))

    result = Backtest(frame(100), Fifty).run()
    assert len(calls) == 50 and len(seen) == 100
    assert len(result.attrs["indicator_snapshot"]["indicators"]) == 50
