"""Visibility, snapshot boundaries, composition, and legacy-interface regressions for direct market-data sources."""

import json
import pickle
import subprocess
import sys
from multiprocessing.pool import ThreadPool
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from test_fluent_indicators import Empty, strategy
from test_indicator_catalog import catalog_data
from test_inputs import request

import openbacktesting as api
from openbacktesting import inputs
from openbacktesting.indicators.types import IndicatorError
from openbacktesting.strategy_data import DATA_NAMES, DERIVED, PRICE_COLUMNS, StrategyData


def advance(owner, length):
    owner._indicator_cursor.phase = "run"
    owner._indicator_cursor.length = length
    owner.data._set_length(length)


@pytest.mark.parametrize("name", [*PRICE_COLUMNS, *DERIVED])
def test_stable_sources_and_slices(name):
    owner = strategy(catalog_data(20))
    saved = getattr(owner, name)
    all_values = np.asarray(saved)
    tail = saved[-3:]
    assert saved is getattr(owner, name)
    assert saved.dtype == np.float64
    assert saved.metadata == {"kind": "data-source", "field": name, "version": "1"}
    assert not owner._indicators and "warmup" not in saved._opts
    advance(owner, 10)
    assert len(saved) == 10
    assert saved[-1] == all_values[9]
    assert saved[-2] == all_values[8]
    assert saved[0] == all_values[0]
    np.testing.assert_array_equal(tail, all_values[7:10])
    advance(owner, 11)
    np.testing.assert_array_equal(tail, all_values[8:11])
    assert len(all_values) == 20


def test_first_access_next_and_complete():
    owner = strategy(catalog_data(20))
    advance(owner, 3)
    saved = owner.close
    assert len(saved) == len(owner.data) == 3
    assert len(owner.data._full_frame()) == 20
    advance(owner, 10)
    assert len(saved) == 10
    owner._indicator_cursor.phase = "complete"
    owner._indicator_cursor.length = 20
    assert len(owner.hl2) == 20
    untouched = api.Backtest(catalog_data(20), Empty).run()["_strategy"]
    assert untouched._strategy_data._baseline is None
    assert len(untouched.close) == 20


def test_pandas_and_pip_delegation_without_snapshot():
    frame = catalog_data(20)
    frame["extra"] = 3
    owner = strategy(frame)
    full_df, full_index = owner.df, owner.data_index
    assert owner.pip == owner.data.pip
    assert owner._strategy_data._baseline is None
    advance(owner, 10)
    saved_df, saved_index = owner.df, owner.data_index
    advance(owner, 11)
    assert len(owner.df) == len(owner.data_index) == 11
    assert len(saved_df) == len(saved_index) == 10
    assert len(full_df) == len(full_index) == 20
    for name in DERIVED:
        getattr(owner, name)
    assert list(owner.df.columns) == list(frame.columns)


@pytest.mark.parametrize("dtype", ["int8", "uint64", "float32", "Int64", "Float64"])
def test_numeric_types_and_integer_overflow(dtype):
    frame = pd.DataFrame(
        {key: pd.Series([120, 120, 120], dtype=dtype) for key in PRICE_COLUMNS.values()}
    )
    owner = strategy(frame)
    for name in (*PRICE_COLUMNS, *DERIVED):
        result = getattr(owner, name)
        assert result.dtype == np.float64
        np.testing.assert_array_equal(result, [120, 120, 120])


@pytest.mark.parametrize(
    "dtype", ["bool", "boolean", "complex128", "object", "str", "category", "datetime64[ns]"]
)
def test_reject_nonreal_types_without_partial_capture(dtype):
    frame = catalog_data(20)
    frame["Volume"] = pd.Series(np.arange(20) % 2, index=frame.index).astype(dtype)
    owner = strategy(frame)
    with pytest.raises(IndicatorError, match="invalid-data-source.*Volume"):
        _ = owner.close
    assert owner._strategy_data._baseline is None
    owner.df["Volume"] = 1.0
    assert len(owner.close) == 20


def test_nullable_missing_and_invalid_derived():
    frame = catalog_data(5)
    frame["Volume"] = pd.array([1, None, 3, 4, 5], dtype="Int64")
    frame["High"] = [10, np.inf, 1e308, 10, 10]
    frame["Low"] = [4, 4, 1e308, np.nan, 4]
    frame["Close"] = [8, 8, 8, 8, np.inf]
    owner = strategy(frame)
    assert np.isnan(owner.volume[1]) and not owner.volume.valid[1]
    assert np.isinf(owner.high[1]) and not owner.high.valid[1]
    for name, expected in (("hl2", 7), ("hlc3", 22 / 3), ("hlcc4", 7.5)):
        result = getattr(owner, name)
        assert result[0] == expected
        assert np.isnan(np.asarray(result)[1:4]).all()
        assert not result.valid[1:4].any()
    assert owner.hl2[4] == 7
    assert np.isnan(owner.hlc3[4]) and np.isnan(owner.hlcc4[4])


@pytest.mark.parametrize("bad", ["index", "missing", "duplicate", "replace"])
def test_invalid_structure(bad):
    frame = catalog_data(5)
    if bad == "index":
        frame.index = [0, 0, 1, 2, 3]
    elif bad == "missing":
        frame = frame.drop(columns="High")
    elif bad == "duplicate":
        frame = pd.concat([frame, frame[["Close"]]], axis=1)
    else:
        frame = frame[list(PRICE_COLUMNS.values())]
        frame.columns = ["Open", "High", "Low", "Close", "Close"]
    with pytest.raises(IndicatorError, match="invalid-data-source"):
        _ = strategy(frame).close


def test_formulas_match_existing_indicators():
    owner = strategy(catalog_data(50))
    for name, method in (("hl2", "hl2"), ("hlc3", "hlc3"), ("hlcc4", "wcp")):
        np.testing.assert_allclose(getattr(owner, name), getattr(owner.ta, method)(), rtol=1e-14)


def test_cached_next_does_not_scan_or_recompute(monkeypatch):
    owner = strategy(catalog_data(30))
    calls = []
    original = StrategyData._derive

    def derive(self, name):
        calls.append(name)
        return original(self, name)

    monkeypatch.setattr(StrategyData, "_derive", derive)
    saved = {name: getattr(owner, name) for name in (*PRICE_COLUMNS, *DERIVED)}
    advance(owner, 2)

    def forbidden(*args, **kwargs):
        pytest.fail("cached getter scanned/copied full data")

    monkeypatch.setattr(owner.data, "_full_frame", forbidden)
    monkeypatch.setattr(pd.DataFrame, "copy", forbidden)
    for length in range(2, 30):
        advance(owner, length)
        for name, handle in saved.items():
            assert getattr(owner, name) is handle and len(handle) == length
    assert calls == list(DERIVED)


@pytest.mark.parametrize(
    "mutation",
    ["value", "dtype", "order", "index", "index_name", "columns_name", "missing", "duplicate"],
)
@pytest.mark.parametrize("boundary", ["read", "indicator", "custom"])
def test_init_mutation_rejected(mutation, boundary):
    owner = strategy(catalog_data(20))
    _ = owner.close
    frame = owner.df
    if mutation == "value":
        frame.iloc[0, 0] += 1
    elif mutation == "dtype":
        frame["Volume"] = frame.Volume.astype("float32")
    elif mutation == "order":
        frame.insert(0, "saved", frame.pop("Volume"))
        frame.rename(columns={"saved": "Volume"}, inplace=True)
    elif mutation == "index":
        frame.index = pd.RangeIndex(len(frame))
    elif mutation == "index_name":
        frame.index.name = "changed"
    elif mutation == "columns_name":
        frame.columns.name = "changed"
    elif mutation == "missing":
        frame.drop(columns="High", inplace=True)
    else:
        frame.insert(0, "High", 1.0, allow_duplicates=True)
    with pytest.raises(IndicatorError, match="data-source-mutated"):
        if boundary == "read":
            _ = owner.open
        elif boundary == "indicator":
            owner.ta.ema()
        else:
            owner.ind(lambda: np.ones(20))


def test_edit_before_source_and_extra_columns():
    owner = strategy(catalog_data(20))
    old = owner.data.Close.copy()
    owner.df["Close"] += 10
    np.testing.assert_allclose(owner.close, old + 10)
    owner.df["extra"] = 1
    assert owner.close is owner.close
    owner.ta.ema(owner.close, length=3)
    owner._strategy_data.validate()


def test_end_init_rejects_before_next():
    class Mutates(Empty):
        def init(self):
            self.saved = self.close
            self.df["High"] += 1

        def next(self):
            pytest.fail("next must not execute")

    with pytest.raises(IndicatorError, match="data-source-mutated"):
        api.Backtest(catalog_data(20), Mutates).run()


def test_runtime_write_preserves_snapshot():
    owner = strategy(catalog_data(20))
    old = np.asarray(owner.close)
    advance(owner, 10)
    owner.data._full_frame()["Close"] += 10
    np.testing.assert_array_equal(owner.close, old[:10])
    assert owner.data._full_frame().Close.iloc[0] != owner.close[0]


@pytest.mark.parametrize("name", sorted(DATA_NAMES))
def test_reserved_assignment_delete_and_parameters(name, monkeypatch):
    owner = strategy()
    for action in (
        lambda: setattr(owner, name, 1),
        lambda: delattr(owner, name),
        lambda: owner._check_params({name: 1}),
    ):
        with pytest.raises(AttributeError, match=f"{name}.*rename"):
            action()
    with pytest.raises(AttributeError, match=f"{name}.*rename"):
        api.Backtest(catalog_data(20), Empty).run(**{name: 1})
    # Optimization rejection occurs before any strategy runs or process pools are created.
    bt = api.Backtest(catalog_data(20), Empty)
    monkeypatch.setattr(bt, "run", lambda **kw: pytest.fail("reserved parameter reached run"))
    with pytest.raises(AttributeError, match=f"{name}.*rename"):
        bt.optimize(**{name: [1, 2]})


@pytest.mark.parametrize("kind", ["field", "method", "property", "input"])
def test_reserved_mro_and_discovery(kind):
    value = {
        "field": 1,
        "method": lambda self: 1,
        "property": property(lambda self: pytest.fail("getter executed")),
        "input": inputs.int(1, title="period"),
    }[kind]
    middle = type("Middle", (Empty,), {"close": value})
    child = type("Child", (middle,), {})
    with pytest.raises(AttributeError, match="close.*rename"):
        child(None, strategy().data, {})
    with pytest.raises(inputs.InputError, match="close.*rename"):
        inputs.describe(child)


def test_input_display_title_and_normal_state(monkeypatch):
    class Declared(Empty):
        period = inputs.int(3, title="close")

    assert inputs.describe(Declared)["inputs"][0]["title"] == "close"
    assert api.Backtest(catalog_data(20), Declared).run()["_strategy"].period == 3
    assert (
        api.Backtest(catalog_data(20), Declared)
        .run_inputs(request(Declared, {"close": 5}))["_strategy"]
        .period
        == 5
    )
    monkeypatch.setattr(api, "Pool", lambda: ThreadPool(2))
    assert api.Backtest(catalog_data(20), Declared).optimize(period=[2, 3])["_strategy"].period in (
        2,
        3,
    )
    owner = strategy()
    owner.note = 1
    del owner.note
    assert not hasattr(owner, "note")


def test_conversion_and_source_rejections():
    owner = strategy(catalog_data(30))
    saved = owner.close
    full = np.asarray(saved)
    full_series, full_df = saved.s, saved.df
    indicator = owner.ta.ema(saved, length=3)
    np.testing.assert_allclose(indicator, owner.ta.ema("Close", length=3), equal_nan=True)
    np.testing.assert_allclose(
        owner.ta.ema(owner.hlcc4, length=3), owner.ta.ema(owner.ta.wcp(), length=3), equal_nan=True
    )
    assert len(owner.ta.ema(saved[:], length=3)) == 30
    for invalid in (
        strategy(catalog_data(30)).close,
        saved[1:],
        owner.ind(lambda: np.ones((2, 30))),
    ):
        with pytest.raises(IndicatorError, match="index-mismatch"):
            owner.ta.ema(invalid, length=3)
    advance(owner, 5)
    assert float(saved) == full[4] and bool(saved)
    assert len(full_series) == len(full_df) == 30
    assert len(saved.s) == len(saved.df) == 5
    assert isinstance(saved + 1, np.ndarray)
    with pytest.raises(ValueError):
        bool(saved > 1)
    for action in (lambda: np.add(saved, 1, out=saved), lambda: np.add.at(saved, 0, 1)):
        with pytest.raises(TypeError):
            action()
    with pytest.raises(TypeError):
        saved[0] = 1
    with pytest.raises(ValueError):
        np.array(saved, copy=False)
    converted = np.asarray(saved)
    assert len(converted) == 5 and not converted.flags.writeable
    assert len(saved.astype("float32")) == 5
    writable = saved.copy()
    writable[0] = -1
    assert saved[0] == full[0]
    base = converted
    while isinstance(base, np.ndarray):
        assert base.size <= 5
        base = base.base
    assert len(base) == 5 * converted.dtype.itemsize
    with pytest.raises(IndicatorError, match="invalid-phase"):
        owner.ta.ema(saved)
    with pytest.raises(IndexError):
        _ = saved[5]
    advance(owner, 0)
    for action in (lambda: saved[-1], lambda: float(saved), lambda: bool(saved)):
        with pytest.raises(IndexError):
            action()


def test_missing_volume_does_not_gate_next():
    class Reads(Empty):
        def init(self):
            self.visited = []
            self.saved = self.volume

        def next(self):
            assert np.isnan(self.saved[-1])
            assert len(self.hl2) == len(self.df)
            self.visited.append(len(self.saved))

    result = api.Backtest(catalog_data(20).drop(columns="Volume"), Reads).run()
    assert result["_strategy"].visited == list(range(1, 21))
    assert result.attrs["indicator_snapshot"]["indicators"] == []

    class Consumes(Reads):
        def init(self):
            super().init()
            self.average = self.ta.ema(self.volume, length=3)

    assert api.Backtest(catalog_data(20).drop(columns="Volume"), Consumes).run()[
        "_strategy"
    ].visited == list(range(1, 21))


class DataTrading(api.Strategy):
    direct = True
    period = 3

    def init(self):
        self.average = self.ta.ema(self.close if self.direct else "Close", length=self.period)
        self.saved = self.close if self.direct else None
        self.visited = []

    def next(self):
        bar = len(self.data)
        self.visited.append(bar)
        if self.direct:
            assert len(self.saved) == len(self.average) == bar
        if bar == 10:
            self.buy(qty=1)
        elif bar == 20:
            self.position.close()


def test_trading_repeat_pickle_and_optimization(monkeypatch):
    bt = api.Backtest(catalog_data(40), DataTrading, end_policy="close_at_last_close")
    old = bt.run(direct=False)
    new, again = bt.run(), bt.run()
    for current in (new, again):
        pd.testing.assert_frame_equal(current["_trades"], old["_trades"])
        pd.testing.assert_frame_equal(current["_equity_curve"], old["_equity_curve"])
        pd.testing.assert_series_equal(current.filter(regex="^[^_]"), old.filter(regex="^[^_]"))
        assert current["_strategy"].visited == old["_strategy"].visited
    assert new["_strategy"].close is not again["_strategy"].close
    restored = pickle.loads(pickle.dumps(new["_strategy"]))
    assert restored.close is restored.saved
    assert restored.saved._cursor is restored.average._cursor is restored._indicator_cursor
    for array in (restored.saved._values, restored._strategy_data._values["high"]):
        with pytest.raises(ValueError):
            array.setflags(write=True)
    advance(restored, 5)
    assert len(restored.saved) == len(restored.average) == 5
    monkeypatch.setattr(api, "Pool", lambda: ThreadPool(2))
    _, old_heat = bt.optimize(period=[3, 5], direct=[False], return_heatmap=True)
    _, new_heat = bt.optimize(period=[3, 5], direct=[True], return_heatmap=True)
    np.testing.assert_array_equal(old_heat, new_heat)


def test_source_exception_and_out_of_money_restore():
    retained = []

    class Fails(Empty):
        def init(self):
            retained.append(self)
            self.saved = self.close

        def next(self):
            raise RuntimeError("user failure")

    with pytest.raises(RuntimeError, match="user failure"):
        api.Backtest(catalog_data(20), Fails).run()
    assert len(retained[-1].saved) == 20
    assert retained[-1]._indicator_cursor.phase == "complete"

    class Ruined(Fails):
        def next(self):
            if len(self.close) == 2:
                self.buy(qty=10)

    frame = pd.DataFrame({key: [100, 100, 100, 1, 1] for key in ("Open", "High", "Low", "Close")})
    with pytest.warns(UserWarning):
        result = api.Backtest(frame, Ruined, cash=100, margin=0.1).run()
    assert result["Equity Final [$]"] == -890
    assert len(retained[-1].saved) == 5
    assert retained[-1]._indicator_cursor.phase == "complete"


def test_real_spawn_sources():
    process = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("strategy_data_spawn_probe.py"))],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert json.loads(process.stdout.splitlines()[-1]) == {"equivalent": True, "active_children": 0}
    assert "resource_tracker" not in process.stderr
