"""Independent references, boundaries, causality, and real strategy consumption for the expanded catalog."""

import builtins
import json
import pickle
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pandas_ta_classic as classic
import pytest

from openbacktesting import Backtest, Strategy, indicators
from openbacktesting.indicators import runtime
from openbacktesting.indicators.api import IndicatorNamespace
from openbacktesting.indicators.calculus import average
from openbacktesting.indicators.common import to_arrays
from openbacktesting.indicators.types import IndicatorCursor, IndicatorError

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (Path(__file__).with_name("fixtures") / "indicator_expansion/contracts.json").read_text()
)
NEW = [row["id"] for row in CONTRACT["entries"]]
FIXTURES = Path(__file__).with_name("fixtures") / "indicator_expansion"


def data(n=320):
    rng = np.random.default_rng(1983)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    result = pd.DataFrame(
        {
            "Open": close + rng.uniform(-0.5, 0.5, n),
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": rng.integers(1, 100, n).astype(float),
        },
        index=pd.date_range("2020-01-01", periods=n, freq="h"),
    )
    result["left"] = result.Close
    result["right"] = result.Close.rolling(4).mean()
    result["source"] = result.Close
    result["condition"] = (np.arange(n) % 7 == 0).astype(float)
    result["anchor"] = (np.arange(n) % 10 == 0).astype(float)
    return result


def compute(name, frame=None, **params):
    return indicators.compute(
        "ta." + name,
        data() if frame is None else frame,
        parameters=params,
        inputs={"source": "source"}
        if "source" in indicators.describe("ta." + name).inputs
        else None,
    )


@pytest.mark.parametrize("name", NEW)
def test_expansion_full_prefix_short_gap_and_no_talib(name, monkeypatch):
    original = builtins.__import__

    def guarded(module, *args, **kwargs):
        if module == "talib":
            pytest.fail("TA-Lib must not be imported")
        return original(module, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    monkeypatch.setitem(classic.Imports, "talib", True)
    frame = data()
    full = indicators.compute(name, frame)
    assert full.shape[-1] == len(frame)
    assert full.s.index.equals(frame.index)
    assert full.metadata["kind"] == indicators.describe(name).kind
    assert full.metadata["backend"] == indicators.describe(name).default_backend
    for n in [0, 1, 2, 5, 19, 100, 217, 319]:
        prefix = indicators.compute(name, frame.iloc[:n])
        np.testing.assert_allclose(np.asarray(full)[..., :n], prefix, equal_nan=True)
        np.testing.assert_array_equal(full.valid[..., :n], prefix.valid)
    gapped = frame.copy()
    gapped.iloc[150, gapped.columns != "anchor"] = np.nan
    gap = indicators.compute(name, gapped)
    assert not np.any(gap.valid & ~np.isfinite(gap))
    if name not in ["ta.pivot_points", "ta.valuewhen"]:
        assert not gap.valid[..., 150].any()
    constant = frame.copy()
    constant[["Open", "High", "Low", "Close", "Volume", "source", "left", "right"]] = 10.0
    flat = indicators.compute(name, constant)
    assert not np.any(flat.valid & ~np.isfinite(flat))
    for key, rule in indicators.describe(name).parameters:
        with pytest.raises(IndicatorError):
            indicators.compute(name, frame, parameters={key: object()})
        values = rule.choices or ([rule.minimum] if rule.minimum is not None else [rule.default])
        for value in values:
            value = int(value) if rule.kind == "int" else value
            parameters = {key: value}
            try:
                indicators.describe(name).normalize(parameters)
            except IndicatorError:
                continue
            result = indicators.compute(name, frame, parameters=parameters)
            prefix = indicators.compute(name, frame.iloc[:217], parameters=parameters)
            np.testing.assert_allclose(np.asarray(result)[..., :217], prefix, equal_nan=True)
            np.testing.assert_array_equal(result.valid[..., :217], prefix.valid)


def test_exact_candidate_inventory_and_frozen_contract():
    record = json.loads(
        (ROOT / "tests/fixtures/engine-indicator-coverage-disposition.json").read_text()
    )
    assert {r["id"] for r in record["candidates"]} == {
        *(f"N{i:02}" for i in range(1, 65)),
        *(f"S{i:02}" for i in range(1, 13)),
        *(f"P{i:02}" for i in range(1, 11)),
    }
    assert len(record["patterns"]) == len({r["id"] for r in record["patterns"]}) == 62
    assert len(record["additional_tv_patterns"]) == 6
    assert len(record["pine_rows"]) == 67
    assert len(record["platform_rows"]) == 284
    assert len(NEW) == len(set(NEW)) == 53
    assert len(indicators.catalog()) == 247
    rows = json.loads((ROOT / "src/openbacktesting/indicators/catalog.json").read_text())["entries"]
    actual = {r["id"]: r for r in rows}
    for row in CONTRACT["entries"]:
        expected = dict(row)
        if row["id"] == "ta.pivot_points":
            # Local built-in extensions explicitly upgrade these three contract fields; other historical fields remain unchanged.
            expected = expected | {
                "version": "2",
                "minimum": 1,
                "parameters": row["parameters"]
                | {"developing": {"default": False, "kind": "bool"}},
            }
        assert actual[row["id"]] == expected


def test_rolling_and_event_hand_values():
    frame = data(5)
    frame["source"] = [5, 2, 5, np.nan, 4]
    np.testing.assert_allclose(
        compute("highestbars", frame, length=3), [np.nan, np.nan, 0, np.nan, np.nan], equal_nan=True
    )
    np.testing.assert_allclose(
        compute("lowestbars", frame, length=3), [np.nan, np.nan, -1, np.nan, np.nan], equal_nan=True
    )
    frame["source"] = [1, 2, 2, 4, 5]
    assert compute("percentrank", frame, length=3)[2] == 100
    assert compute("percentile_nearest_rank", frame, length=3, percentage=50)[2] == 2
    assert compute("percentile_linear_interpolation", frame, length=2, percentage=50)[1] == 1.5
    np.testing.assert_allclose(compute("rolling_sum", frame, length=3)[2:], [5, 8, 11])
    np.testing.assert_allclose(compute("range", frame, length=3)[2:], [1, 2, 3])
    frame["condition"] = [1, 0, np.nan, 0, 1]
    np.testing.assert_allclose(
        compute("barssince", frame), [0, 1, np.nan, np.nan, 0], equal_nan=True
    )
    np.testing.assert_allclose(
        compute("valuewhen", frame), [1, 1, np.nan, np.nan, 5], equal_nan=True
    )
    frame["condition"] = [1, 1, 1, 0, 1]
    frame["source"] = [2, np.nan, 3, np.nan, 4]
    np.testing.assert_allclose(
        compute("valuewhen", frame, occurrence=1), [np.nan, 2, np.nan, np.nan, 3], equal_nan=True
    )
    frame["source"] = [1, np.nan, 2, -1, 4]
    np.testing.assert_allclose(compute("cum", frame), [1, np.nan, 3, 2, 6], equal_nan=True)
    np.testing.assert_allclose(compute("running_max", frame), [1, np.nan, 2, 2, 4], equal_nan=True)
    np.testing.assert_allclose(
        compute("running_min", frame), [1, np.nan, 1, -1, -1], equal_nan=True
    )
    frame["condition"] = 2
    for name in ["barssince", "valuewhen", "rolling_count", "pivot_points"]:
        if name == "pivot_points":
            frame["anchor"] = 2
        with pytest.raises(IndicatorError, match="invalid-input"):
            compute(name, frame)


def test_cross_equal_boundary_and_rising_not_monotonic():
    frame = data(4)
    frame["left"], frame["right"] = [1, 2, 1, 0], [1, 1, 1, 1]
    np.testing.assert_allclose(compute("cross", frame), [np.nan, 1, 0, 1], equal_nan=True)
    np.testing.assert_allclose(compute("crossover", frame), [np.nan, 1, 0, 0], equal_nan=True)
    np.testing.assert_allclose(compute("crossunder", frame), [np.nan, 0, 0, 1], equal_nan=True)
    frame["source"] = [3, 1, 2, 4]
    assert compute("rising", frame, length=3)[-1] == 1
    frame["source"] = [2, 4, 3, 1]
    assert compute("falling", frame, length=3)[-1] == 1
    for name in ["change", "shift"]:
        with pytest.raises(IndicatorError):
            compute(name, frame, length=-1)


def test_confirmed_pivot_timing_ties_and_low():
    frame = data(8)
    frame["High"] = [1, 2, 5, 3, 2, 5, 5, 1]
    result = compute("pivothigh", frame, left=2, right=2)
    assert result["value"][4] == 5
    assert result["pivot_bar"][4] == 2
    assert result["confirmed_at"][4] == 4
    assert not result.valid[:, :4].any()
    assert result.metadata["required_outputs"] == []
    assert "warmup" not in result._opts
    # Equal extrema confirm only after the rightmost candidate's right window completes.
    result = compute("pivothigh", frame, left=1, right=1)
    assert not result["value"].valid[6]
    assert result["value"][7] == 5
    frame["Low"] = -frame.High
    np.testing.assert_allclose(
        compute("pivotlow", frame, left=1, right=1)["value"],
        -np.asarray(result["value"]),
        equal_nan=True,
    )


def test_reference_smi_pmo_and_stock_fixed_values():
    frame = pd.read_csv(FIXTURES / "quotes.csv", index_col=0, parse_dates=True)
    frame.columns = [c.title() for c in frame.columns]
    for name, file in [("smi_stochastic", "smi"), ("pmo", "pmo")]:
        expected = pd.read_json(FIXTURES / (file + ".json"))
        expected = expected.drop(columns="timestamp").to_numpy(dtype=float).T
        actual = compute(name, frame)
        np.testing.assert_allclose(actual, expected, equal_nan=True, rtol=1e-10, atol=1e-10)
    assert compute("crsi", frame)[-1] == pytest.approx(74.7662, abs=0.0001)
    assert compute("crsi", frame, length=14, streak=20, rank=10)[-1] == pytest.approx(
        61.6053, abs=0.0001
    )
    stop = compute("atr_stop", frame)
    for bar, value in {
        21: 211.13,
        151: 232.7861,
        152: 236.3913,
        249: 253.8863,
        501: 246.3232,
    }.items():
        assert stop["stop"][bar] == pytest.approx(value, abs=0.0001)
    volatility = compute("volatility_stop", frame, length=14)
    for bar, value in {
        54: 226.2118,
        55: 226.2124,
        282: 261.8687,
        283: 249.3219,
        284: 249.7460,
    }.items():
        assert volatility["stop"][bar] == pytest.approx(value, abs=0.0001)


def test_small_ordinary_formula_fixtures():
    frame = data(12)
    frame["Close"] = np.arange(1, 13, dtype=float)
    frame["High"], frame["Low"], frame["Open"] = frame.Close + 2, frame.Close - 2, frame.Close - 1
    frame["Volume"] = [10] * 11 + [100]
    assert compute("rvol", frame, length=3)[-1] == 10
    assert compute("adr", frame, length=2)[-1] == 4
    assert compute("ibs", frame)[-1] == 0.5
    assert compute("iii", frame)[-1] == 0
    assert compute("wvad", frame)[-1] == 25
    assert compute("rci", frame, length=3)[-1] == pytest.approx(100)
    assert compute("rmi", frame, length=2, momentum=2)[-1] == 100
    assert compute("ac", frame, fast=2, slow=4, signal=2)[-1] == 0
    envelope = compute("ma_envelopes", frame, length=2, percent=10)
    np.testing.assert_allclose(np.asarray(envelope)[:, -1], [11.5, 12.65, 10.35])
    frame["Close"] = 10.0
    frame["High"], frame["Low"] = 12.0, 8.0
    stop = compute("starc", frame, length=2, atr_length=2, multiplier=2)
    np.testing.assert_allclose(np.asarray(stop)[:, -1], [10, 18, 2])
    np.testing.assert_allclose(
        np.asarray(compute("alligator", frame, jaw=3, teeth=2, lips=1))[:, -1], [10, 10, 10]
    )
    np.testing.assert_allclose(
        np.asarray(compute("gator", frame, jaw=3, teeth=2, lips=1))[:, -1], [0, 0]
    )
    np.testing.assert_allclose(compute("frama", frame, length=4)[3:], 10)
    frame[["High", "Low"]] = 10.0
    np.testing.assert_allclose(compute("frama", frame, length=4)[3:], 10)
    with pytest.raises(IndicatorError, match="even"):
        compute("frama", frame, length=3)
    frame["Close"] = [1, 2, 2, 1, 3, 2, 4, 3, 2, 3, 4, 5]
    # Average ranks for [1,2,2] are [1,2.5,2.5], with an independent Pearson calculation.
    assert compute("rci", frame, length=3)[2] == pytest.approx(86.6025403784)
    wave = compute("wavetrend", frame, length=1, average=1, signal=1)
    assert not wave.valid.any()  # price exactly equals the first EMA stage, so the denominator is 0.


def test_pivot_period_formulas_and_missing_levels():
    frame = data(6)
    frame[["Open", "High", "Low", "Close"]] = [
        [8, 11, 7, 9],
        [9, 12, 6, 10],
        [20, 22, 19, 21],
        [21, 40, 5, 30],
        [30, 32, 29, 31],
        [31, 33, 30, 32],
    ]
    frame["anchor"] = [1, 0, 1, 0, 1, 0]
    expected = {
        "traditional": [
            28 / 3,
            38 / 3,
            20 / 3,
            46 / 3,
            10 / 3,
            56 / 3,
            2 / 3,
            22,
            -2,
            76 / 3,
            -14 / 3,
        ],
        "fibonacci": [
            28 / 3,
            28 / 3 + 0.382 * 6,
            28 / 3 - 0.382 * 6,
            28 / 3 + 0.618 * 6,
            28 / 3 - 0.618 * 6,
            46 / 3,
            10 / 3,
        ],
        "woodie": [14.5, 23, 17, 20.5, 8.5, 29, 11, 35, 5],
        "classic": [28 / 3, 38 / 3, 20 / 3, 46 / 3, 10 / 3, 64 / 3, -8 / 3, 82 / 3, -26 / 3],
        "demark": [10, 14, 8],
        "camarilla": [28 / 3, 10.55, 9.45, 11.1, 8.9, 11.65, 8.35, 13.3, 6.7, 20, 0],
    }
    for method, values in expected.items():
        result = compute("pivot_points", frame, method=method)
        np.testing.assert_allclose(np.asarray(result)[: len(values), 2], values)
        np.testing.assert_allclose(
            np.asarray(result)[:, 2], np.asarray(result)[:, 3], equal_nan=True
        )
        assert not result.valid[len(values) :, 2].any()
        assert not result.valid[:, :2].any()
    frame.loc[frame.index[0], "anchor"] = 0
    assert not compute("pivot_points", frame).valid[:, :4].any()
    frame.loc[frame.index[2], "High"] = np.nan
    assert not compute("pivot_points", frame).valid[:, 4:].any()
    frame["anchor"] = np.nan
    with pytest.raises(IndicatorError, match="anchor"):
        compute("pivot_points", frame)


def pattern_frame(name):
    candles = [[10, 11, 9, 10.2]] * 20
    suffix = {
        "doji": [[10, 11, 9, 10.05]],
        "inside": [[10, 10.5, 9.5, 10.1]],
        "engulfing": [[10.8, 11, 9.8, 10], [9.9, 11, 9.8, 10.9]],
        "hammer": [[9, 9.11, 8.5, 9.1]],
        "shootingstar": [[10.5, 11.3, 10.49, 10.6]],
        "harami": [[11, 11.2, 8.8, 9], [9.9, 10.2, 9.8, 10]],
        "morningstar": [[11, 11.2, 8.8, 9], [8.5, 8.7, 8.3, 8.6], [8.7, 10.3, 8.6, 10.2]],
        "eveningstar": [[9, 11.2, 8.8, 11], [11.5, 11.7, 11.3, 11.4], [11.3, 11.4, 9.7, 9.8]],
        "marubozu": [[9, 11.01, 8.99, 11]],
    }[name]
    frame = pd.DataFrame(candles + suffix, columns=["Open", "High", "Low", "Close"])
    frame["Volume"] = 1.0
    return frame


@pytest.mark.parametrize(
    "name,expected",
    [
        ("doji", 100),
        ("inside", 1),
        ("engulfing", 100),
        ("hammer", 100),
        ("shootingstar", -100),
        ("harami", 100),
        ("morningstar", 100),
        ("eveningstar", -100),
        ("marubozu", 100),
    ],
)
def test_nonzero_pattern_fixtures(name, expected):
    frame = pattern_frame(name)
    result = compute("cdl_" + name, frame)
    assert result.dtype == np.dtype("int16")
    assert result[-1] == expected and result.valid[-1]
    assert not result.valid[0]
    assert result[0] == 0
    # Appending the same pattern leaves its original trigger time and score unchanged.
    extended = pd.concat([frame, frame], ignore_index=True)
    np.testing.assert_array_equal(compute("cdl_" + name, extended)[: len(frame)], result)
    if name in ["inside", "engulfing", "harami", "marubozu"]:
        inverse = frame.copy()
        inverse.Open = 20 - frame.Open
        inverse.Close = 20 - frame.Close
        inverse.High = 20 - frame.Low
        inverse.Low = 20 - frame.High
        assert compute("cdl_" + name, inverse)[-1] == -expected
    frame.loc[len(frame) - 1, ["Open", "High", "Low", "Close"]] = [100, 110, 80, 90]
    assert compute("cdl_" + name, frame)[-1] == 0


def test_revised_indexes_and_parameters():
    frame = data(3)
    frame.Close = [100, 110, 121]
    for name, volume in [("nvi", [300, 200, 100]), ("pvi", [100, 200, 300])]:
        frame.Volume = volume
        result = compute(name, frame)
        np.testing.assert_allclose(result, [1000, 1100, 1210])
        assert result.metadata["semantic_version"] == "2"
        assert result.metadata["implementation_version"] == "2"
        frame.Volume = 100
        np.testing.assert_allclose(compute(name, frame), [1000] * 3)
    with pytest.raises(IndicatorError):
        compute("msw", period=1)
    for name in ["squeeze", "squeeze_pro"]:
        frame = data()
        frame.iloc[100:, frame.columns.get_indexer(["Open", "High", "Low", "Close"])] += 100
        yes, no = compute(name, frame, use_tr=True), compute(name, frame, use_tr=False)
        assert np.any(np.asarray(yes)[1:] != np.asarray(no)[1:])


def test_new_inputs_strategy_gating_and_pickle():
    class Mixed(Strategy):
        def init(self):
            self.fast = self.ta.ema(length=2)
            self.slow = self.ta.ema(length=3)
            self.crossed = self.ta.crossover(self.fast, self.slow)
            self.saved = self.ta.valuewhen(self.crossed, self.fast)
            self.pivot = self.ta.pivothigh(left=1, right=1)
            self.doji = self.ta.cdl_doji(length=2)
            self.seen = []

        def next(self):
            assert len(self.crossed) == len(self.data)
            self.seen.append((len(self.data), self.saved[-1], self.pivot.value.valid[-1]))

    frame = data(20)
    frame[["Open", "High", "Low", "Close"]] = 10.0
    for budget in [0, 64 * 1024 * 1024]:
        strategy = Backtest(frame, Mixed, indicator_cache_bytes=budget).run()["_strategy"]
        assert len(strategy.seen) > 10
        assert not strategy.pivot.value.valid.any()
        assert not strategy.saved.valid.any()
        copied = pickle.loads(pickle.dumps(strategy.pivot.value))
        np.testing.assert_array_equal(copied.valid, strategy.pivot.value.valid)
        assert not np.asarray(copied).flags.writeable

    def register(indicator, **kwargs):
        params = {
            k: v for k, v in kwargs.items() if k not in ["inputs", "backend", "required_outputs"]
        }
        return indicators.compute(
            indicator,
            frame,
            parameters=params,
            **{k: kwargs[k] for k in ["inputs", "backend", "required_outputs"]},
        )

    namespace = IndicatorNamespace(register)
    with pytest.raises(IndicatorError, match="both be specified"):
        namespace._call_inputs("ta.cross", {"left": "Close"}, {"right": "Open"}, None, None, {})
    with pytest.raises(IndicatorError):
        namespace._call_inputs("ta.cross", {"left": np.ones(20)}, None, None, None, {})
    result = namespace._call_inputs(
        "ta.cross",
        {"left": None, "right": None},
        {"left": "Close", "right": "Open"},
        None,
        None,
        {},
    )
    assert not np.asarray(result[1:]).any()


def test_definition_masks_and_average_contract_edges():
    spec = indicators.describe("ta.ema")
    for fields in [
        {"kind": "unknown"},
        {"validity": "bad"},
        {"input_args": ("bad",)},
        {"input_args": ("close", "close")},
        {"input_defaults": (("missing", "Close"),)},
        {"input_defaults": (("close", "Close"), ("close", "Open"))},
    ]:
        with pytest.raises(ValueError):
            replace(spec, **fields)
    frame = data(3)
    result = pd.Series([1, 2, 3], index=frame.index, name="ema")
    for mask in [np.ones(3), np.ones(4, dtype=bool)]:
        result.attrs["indicator_valid"] = mask
        with pytest.raises(IndicatorError, match="validity mask"):
            to_arrays(spec, result, frame.index, {"length": 1})
    np.testing.assert_allclose(
        average(pd.Series([1, 2, np.nan, 3, 5]), 2),
        [np.nan, 1.5, np.nan, np.nan, 4],
        equal_nan=True,
    )
    assert not compute("cdl_doji", frame.iloc[:1], length=2).valid.any()
    cache = runtime.IndicatorCache()
    cursor = IndicatorCursor(3)
    parent = indicators.compute("ta.cdl_doji", frame, parameters={"length": 2}, cursor=cursor)
    result = indicators.compute(
        "ta.cum", frame, inputs={"source": parent}, cursor=cursor, cache=cache
    )
    assert not result.valid[:2].any()  # Invalid integer placeholders must become missing values during composition.


@pytest.mark.parametrize("name", ["nvi", "pvi"])
def test_price_volume_index_gap_seed_zero_and_lag(name):
    frame = data(9)
    frame.Close = [np.nan, 10, 20, 30, 0, 40, 80, 160, 320]
    volume = np.arange(9, dtype=float) + 1
    frame.Volume = -volume if name == "nvi" else volume
    result = compute(name, frame)
    np.testing.assert_allclose(
        result, [np.nan, 1000, 2000, 3000, 0, np.nan, 0, 0, 0], equal_nan=True
    )
    frame.Close = [10, 20, 40, 80, 160, 320, 640, 1280, 2560]
    result = compute(name, frame, length=2)
    np.testing.assert_allclose(
        result,
        [1000, np.nan, 4000, 16000, 64000, 256000, 1024000, 4096000, 16384000],
        equal_nan=True,
    )
    frame.loc[frame.index[3], "Volume"] = np.nan
    result = compute(name, frame)
    assert not result.valid[3:5].any()
    assert result[5] == 8000


def test_pivot_demark_equality_decline_and_zero_camarilla():
    frame = data(3)
    frame.Open = [10, 10, 20]
    frame.High = [12, 12, 22]
    frame.Low = [6, 6, 18]
    frame.Close = [10, 10, 21]
    frame.anchor = [1, 0, 1]
    assert compute("pivot_points", frame, method="demark")["p"][-1] == 9.5
    frame.loc[frame.index[1], "Close"] = 8
    assert compute("pivot_points", frame, method="demark")["p"][-1] == 8
    frame.loc[frame.index[0], "Low"] = 0
    result = compute("pivot_points", frame, method="camarilla")
    assert result["p"].valid[-1] and not result["r5"].valid[-1]
    frame.loc[frame.index[-1], "Open"] = np.nan
    assert not compute("pivot_points", frame, method="woodie").valid[:, -1].any()
    frame.anchor = 1
    frame.loc[frame.index[-1], "Open"] = 20
    assert compute("pivot_points", frame)["p"].valid[1:].all()


def expansion_process_result(name):
    result = indicators.compute(name, data(180))
    copied = pickle.loads(pickle.dumps(result))
    return np.asarray(copied), copied.valid, copied.ready, copied.metadata


def test_new_category_thread_spawn_and_cache_equivalence():
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

    names = ["ta.crsi", "ta.pivothigh", "ta.valuewhen", "ta.pivot_points", "ta.cdl_engulfing"]
    expected = [expansion_process_result(name) for name in names]
    with ThreadPoolExecutor(2) as pool:
        threaded = list(pool.map(expansion_process_result, names))
    with ProcessPoolExecutor(1, mp_context=multiprocessing.get_context("spawn")) as pool:
        spawned = list(pool.map(expansion_process_result, names))
    for results in [threaded, spawned]:
        for a, b in zip(expected, results):
            for left, right in zip(a[:3], b[:3]):
                np.testing.assert_array_equal(left, right)
            assert a[3] == b[3]
    frame = data(180)
    for budget in [0, 1, 64 * 1024 * 1024]:
        cache = runtime.IndicatorCache(budget)
        for name, expected_result in zip(names, expected):
            first = indicators.compute(name, frame, cache=cache)
            second = indicators.compute(name, frame, cache=cache)
            np.testing.assert_array_equal(first, expected_result[0])
            np.testing.assert_array_equal(second.valid, expected_result[1])
            assert cache.bytes <= budget
        assert cache.hits == (len(names) if budget > 1 else 0)


def test_expanded_user_example_executes_without_future_reads(monkeypatch):
    import runpy

    example = runpy.run_path(str(ROOT / "examples/strategies/confirmed_events.py"))
    strategy = example["ExpandedSignals"]
    original = strategy.next
    seen = []
    confirmed = []

    def checked_next(self):
        size = len(self.close)
        assert len(self.fast) == len(self.slow) == size
        if self.pivot.value.valid[-1]:
            assert self.pivot.confirmed_at[-1] == size - 1
            assert self.pivot.pivot_bar[-1] == size - 4
            confirmed.append(size)
        seen.append(size)
        original(self)

    monkeypatch.setattr(strategy, "next", checked_next)
    from example_support import example_chart

    from openbacktesting import runtime

    result = runtime.run(example, **example_chart(example))
    assert len(seen) > 1000 and confirmed
    assert seen == list(range(seen[0], len(example_chart(example)["data"]) + 1))
    frame = example_chart(example)["data"]
    expected_anchors = ~frame.index.to_period("M").duplicated()
    np.testing.assert_array_equal(frame.PeriodStart, expected_anchors)
    # Month-start levels use only the previous complete input month; subsequent highs/lows cannot rewrite them.
    strategy = result["_strategy"]
    levels = np.asarray(strategy.levels.p)
    starts = np.flatnonzero(expected_anchors)
    for i in range(1, len(starts) - 1):
        left, right = starts[i : i + 2]
        previous = frame.iloc[starts[i - 1] : left]
        expected = (previous.High.max() + previous.Low.min() + previous.Close.iloc[-1]) / 3
        np.testing.assert_allclose(levels[left:right], expected)


def test_mixed_strategy_trades_stats_and_event_times_cache_independent():
    class Trading(Strategy):
        def init(self):
            self.first = self.ta.ema(length=2)
            self.other = self.ta.ema(length=5)
            self.buy_signal = self.ta.crossover(self.first, self.other)
            self.sell_signal = self.ta.crossunder(self.first, self.other)
            self.pattern = self.ta.cdl_engulfing()
            self.pivot = self.ta.pivothigh(left=1, right=1)
            self.event_times = []

        def next(self):
            if self.pivot.value.valid[-1]:
                self.event_times.append((self.pivot.pivot_bar[-1], self.pivot.confirmed_at[-1]))
            if self.buy_signal[-1] and not self.position:
                self.buy(qty=1)
            elif self.sell_signal[-1] and self.position:
                self.position.close()

    results = [
        Backtest(
            data(), Trading, indicator_cache_bytes=budget, end_policy="close_at_last_close"
        ).run()
        for budget in [0, 1, 64 * 1024 * 1024]
    ]
    assert results[0]["# Trades"] > 0
    assert results[0]["_strategy"].event_times
    for result in results[1:]:
        pd.testing.assert_frame_equal(result["_trades"], results[0]["_trades"])
        pd.testing.assert_frame_equal(result["_equity_curve"], results[0]["_equity_curve"])
        pd.testing.assert_series_equal(
            result.filter(regex="^[^_]"), results[0].filter(regex="^[^_]")
        )
        assert result["_strategy"].event_times == results[0]["_strategy"].event_times


@pytest.mark.parametrize("name", ["engulfing", "harami"])
def test_pattern_touching_body_retains_eighty_strength(name):
    frame = pattern_frame(name)
    if name == "engulfing":
        frame.loc[len(frame) - 1, "Open"] = frame.Close.iloc[-2]
    else:
        frame.loc[len(frame) - 1, "Open"] = frame.Close.iloc[-2]
        frame.loc[len(frame) - 1, "Close"] = frame.Close.iloc[-2] + 0.1
    result = compute("cdl_" + name, frame)
    assert result[-1] == 80 and result.valid[-1]


def test_doji_exact_threshold_and_native_gap_rewarm():
    frame = data(20)
    frame.Open = 10.0
    frame.Close = 10.0
    frame.High = 12.0
    frame.Low = 8.0
    frame.loc[frame.index[-1], "Close"] = 10.5
    assert compute("cdl_doji", frame, length=3, factor=12.5)[-1] == 100
    frame.loc[frame.index[-1], "Close"] = np.nextafter(10.5, np.inf)
    assert compute("cdl_doji", frame, length=3, factor=12.5)[-1] == 0
    frame.loc[frame.index[10], "Open"] = np.nan
    result = compute("cdl_harami", frame)
    assert not result.valid[10:].any()
    frame.loc[:, ["Open", "High", "Low", "Close"]] = np.nan
    assert not compute("cdl_harami", frame).valid.any()
