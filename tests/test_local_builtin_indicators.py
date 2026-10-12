"""局部指标扩展：手算、拒绝域、每前缀因果性及真实句柄。"""

from collections import Counter

import numpy as np
import pandas as pd
import pytest
from openbacktesting import Backtest, Strategy
from openbacktesting.indicators import IndicatorCache, compute
from openbacktesting.indicators.statistics.mode import _ModeWindow
from openbacktesting.indicators.types import IndicatorError
from test_local_builtin_baseline import DEFAULTS, baseline_data


def calculate(name, frame, **params):
    return compute("ta." + name, frame, parameters=params)


def vwap_frame(source, volume, anchor):
    return pd.DataFrame({"source": source, "Volume": volume, "anchor": anchor})


def test_tr_fallback_current_close_and_invalid_ranges():
    frame = pd.DataFrame(
        {
            "High": [10, 12, 13, np.nan, 5, np.inf],
            "Low": [10, 9, 8, 2, 6, 1],
            "Close": [8, np.nan, 9, 3, 5, 1],
        }
    )
    h = calculate("true_range", frame, handle_na=True)
    np.testing.assert_allclose(h[:3], [0, 4, 5])
    assert h.valid[:3].all() and not h.valid[3:].any()
    h = calculate("true_range", frame, handle_na=True, drift=2)
    np.testing.assert_allclose(h[:3], [0, 3, 5])
    assert h.valid[1]


def test_vwap_hand_calculation_resets_and_bands():
    f = vwap_frame([10.0, 20.0, 30.0], [1.0, 3.0, 1.0], [1.0, 0.0, 1.0])
    h = calculate("anchored_vwap", f)
    np.testing.assert_allclose(h, [10, 17.5, 30])
    b = calculate("anchored_vwap_bands", f, stdev_mult=2.0)
    np.testing.assert_allclose(b["vwap"], h)
    assert b["upper"][1] == pytest.approx(17.5 + 2 * np.sqrt(18.75))
    assert b["lower"][1] == pytest.approx(17.5 - 2 * np.sqrt(18.75))
    np.testing.assert_allclose(np.asarray(b)[:, [0, 2]], [[10, 30]] * 3)
    zero = calculate("anchored_vwap_bands", f, stdev_mult=0.0)
    np.testing.assert_allclose(zero[0], zero[1])
    np.testing.assert_allclose(zero[1], zero[2])
    f["anchor"] = [0, 1, 1]
    np.testing.assert_allclose(calculate("anchored_vwap", f), [np.nan, 20, 30], equal_nan=True)


def test_vwap_missing_zero_negative_and_numerical_failure():
    f = vwap_frame(
        [5, np.nan, 20, 21, np.nan, 30, 40], [0, 1, 2, 0, 3, np.nan, 2], [1, 1, 0, 0, 0, 0, 0]
    )
    np.testing.assert_allclose(
        calculate("anchored_vwap", f), [np.nan, np.nan, 20, 20, np.nan, np.nan, 30], equal_nan=True
    )
    for bad in (-1.0,):
        with pytest.raises(IndicatorError, match="invalid-input"):
            calculate("anchored_vwap", f.assign(Volume=bad))
    for bad in (np.nan, np.inf, 2.0):
        with pytest.raises(IndicatorError, match="invalid-input"):
            calculate("anchored_vwap", f.assign(anchor=bad))
    for source, volume in [([1, 2], [1e308, 1e308]), ([1e308, -1e308], [1, 1])]:
        with pytest.raises(IndicatorError, match="calculation-failed"):
            calculate("anchored_vwap", vwap_frame(source, volume, [1, 0]))
    stable = calculate("anchored_vwap_bands", vwap_frame([1e12, 1e12 + 2], [1, 1], [1, 0]))
    assert stable["upper"][1] == 1e12 + 2


def test_mode_finite_window_and_bounded_state():
    f = pd.DataFrame({"Close": [1, 0, 1, 0, -1, np.nan, np.inf, 4, 2, 3]})
    np.testing.assert_allclose(
        calculate("mode", f), [np.nan] * 4 + [0, 0, 0, 0, -1, -1], equal_nan=True
    )
    np.testing.assert_allclose(
        calculate("mode", pd.DataFrame({"Close": [4, 2, 3]}), length=3),
        [np.nan, np.nan, 2],
        equal_nan=True,
    )
    window = _ModeWindow(7)
    observed = []
    for value in np.random.default_rng(7).integers(0, 12, 400):
        window.add(float(value))
        observed.append(float(value))
        assert len(window.queue) <= 7 and len(window.heap) <= 28 and len(window.counts) <= 7
        if len(observed) >= 7:
            counts = Counter(observed[-7:])
            expected = min(counts, key=lambda x: (-counts[x], x))
            assert window.value() == expected
    flat = calculate("mode", pd.DataFrame({"Close": [np.nan] + [1.0] * 50}), length=1)
    assert not flat.valid[0] and flat.valid[1:].all()


@pytest.mark.parametrize("mamode", ["sma", "ema", "rma", "wma"])
def test_kc_range_option_changes_gap(mamode):
    f = baseline_data("gap")
    tr = calculate("kc", f, length=5, mamode=mamode, use_true_range=True)
    hl = calculate("kc", f, length=5, mamode=mamode, use_true_range=False)
    assert tr["upper"][24] > hl["upper"][24]
    np.testing.assert_allclose(tr["middle"], hl["middle"], equal_nan=True)


def test_alma_weight_center_and_degenerate_windows():
    f = pd.DataFrame({"Close": np.arange(1, 13, dtype=float)})
    h = calculate("alma", f, length=10, sigma=6.0, distribution_offset=0.85, floor=True)
    w = np.exp(-((np.arange(10) - 7) ** 2) / (2 * (10 / 6) ** 2))
    w /= w.sum()
    assert h[9] == pytest.approx(np.arange(1, 11) @ w[::-1])
    assert h[9] != pytest.approx(calculate("alma", f, length=10)[9])
    np.testing.assert_allclose(calculate("alma", f, length=1, floor=True), f.Close)
    assert not calculate("alma", f.iloc[:2], length=10, floor=True).valid.any()
    g = f.copy()
    g.iloc[3] = np.inf
    assert not calculate("alma", g, length=5, floor=True).valid[4:8].any()
    sharp = calculate("alma", f, length=5, floor=True, sigma=1e308)
    assert np.isfinite(sharp[4:]).all()


@pytest.mark.parametrize("offset,expected", [(0, 3), (1, 2), (-1, 4), (2, 1), (5, -2)])
def test_linreg_position_not_shift(offset, expected):
    h = calculate("linreg", pd.DataFrame({"Close": [1.0, 2.0, 3.0]}), length=3, offset=offset)
    assert h[-1] == pytest.approx(expected)
    assert not h.valid[:2].any()


def test_linreg_parameter_domain_and_short():
    f = baseline_data("normal")
    for bad in (True, 1.2, 10**400):
        with pytest.raises(IndicatorError, match="invalid-parameter"):
            calculate("linreg", f, offset=bad)
    assert not calculate("linreg", f.iloc[:2], offset=1).valid.any()
    assert not calculate("linreg", f, offset=1, length=1).valid.any()
    huge = pd.DataFrame({"Close": [1.0, 2.0, 3.0]})
    # 有限参数仍可能造成输出溢出。
    huge["Close"] = [1.0, 10.0, 20.0]
    assert not calculate("linreg", huge, length=3, offset=10**308).valid[-1]


@pytest.mark.parametrize("method", ["traditional", "fibonacci", "classic", "demark", "camarilla"])
def test_pivot_developing_prefix_and_invalid_segment(method):
    f = baseline_data("normal").iloc[:8].copy()
    f["anchor"] = [1, 0, 0, 0, 1, 0, 0, 0]
    full = calculate("pivot_points", f, method=method, developing=True)
    assert full["p"].valid[0]
    if method == "traditional":
        assert full["p"][0] == pytest.approx((f.High.iloc[0] + f.Low.iloc[0] + f.Close.iloc[0]) / 3)
    for n in range(1, len(f) + 1):
        h = calculate("pivot_points", f.iloc[:n], method=method, developing=True)
        np.testing.assert_allclose(np.asarray(full)[..., :n], h, equal_nan=True)
        np.testing.assert_array_equal(full.valid[..., :n], h.valid)
    g = f.copy()
    g.iloc[1, g.columns.get_loc("High")] = np.nan
    h = calculate("pivot_points", g, method=method, developing=True)
    assert not h["p"].valid[1:4].any() and h["p"].valid[4:].all()
    g = f.copy()
    g.loc[g.index[1], "High"] = g.Low.iloc[1] - 1
    assert not calculate("pivot_points", g, method=method, developing=True)["p"].valid[1:4].any()


def test_pivot_woodie_rejected_and_anchor_delay():
    f = baseline_data("normal")
    f["anchor"] = 0.0
    f.loc[f.index[2], "anchor"] = 1.0
    h = calculate("pivot_points", f, developing=True)
    assert not h["p"].valid[:2].any() and h["p"].valid[2]
    with pytest.raises(IndicatorError, match="invalid-parameter"):
        calculate("pivot_points", f, method="woodie", developing=True)


OPTIONS = [
    ("true_range", {"handle_na": True}),
    ("kc", {"use_true_range": False}),
    ("alma", {"floor": True}),
    ("linreg", {"offset": -2}),
    ("pivot_points", {"developing": True}),
    ("anchored_vwap", {}),
    ("anchored_vwap_bands", {"stdev_mult": 2.0}),
    ("mode", {"length": 3}),
]


@pytest.mark.parametrize("name,params", OPTIONS)
def test_full_prefix_cache_and_domains(name, params):
    f = baseline_data("normal")
    f["source"] = f.Close
    full = calculate(name, f, **params)
    for n in (0, 1, 2, 5, 16, 29):
        prefix = calculate(name, f.iloc[:n], **params)
        np.testing.assert_allclose(np.asarray(full)[..., :n], prefix, equal_nan=True)
        np.testing.assert_array_equal(full.valid[..., :n], prefix.valid)
    cache = IndicatorCache()
    first = compute("ta." + name, f, parameters=params, cache=cache)
    second = compute("ta." + name, f, parameters=params, cache=cache)
    assert cache.hits == 1
    np.testing.assert_array_equal(first.valid, second.valid)
    if name in DEFAULTS:
        compute("ta." + name, f, cache=cache)
        assert cache.misses == 2
    with pytest.raises(IndicatorError, match="invalid-parameter"):
        calculate(name, f, nonesuch=True)
    if params:
        key = next(iter(params))
        with pytest.raises(IndicatorError, match="invalid-parameter"):
            calculate(name, f, **{key: "invalid"})
    if name == "anchored_vwap_bands":
        for x in (-1.0, np.inf, True):
            with pytest.raises(IndicatorError):
                calculate(name, f, stdev_mult=x)


def test_method_handles_and_input_boundaries():
    f = baseline_data("normal")
    f["Reset"] = f.anchor
    f["Regime"] = (np.arange(len(f)) % 3).astype(float)

    class Mixed(Strategy):
        def init(self):
            self.v = self.ta.anchored_vwap(
                inputs={"source": self.hlc3, "volume": self.volume, "anchor": "Reset"}
            )
            self.b = self.ta.anchored_vwap_bands(
                inputs={"source": self.hlc3, "volume": self.volume, "anchor": "Reset"}
            )
            self.m = self.ta.mode("Regime", length=3)
            self.t = self.ta.true_range(handle_na=True)
            self.a = self.ta.alma(floor=True)
            self.k = self.ta.kc(use_true_range=False)
            self.r = self.ta.linreg(offset=1)
            self.p = self.ta.pivot_points(developing=True, inputs={"anchor": "Reset"})
            self.saved = self.v
            self.seen = []

        def next(self):
            assert len(self.saved) == self.bar_index + 1
            assert self.t.valid[0]
            if self.b.vwap.valid[-1]:
                assert self.b.vwap[-1] == pytest.approx(self.v[-1])
            self.seen.append(float(self.v[-1]))

    bt = Backtest(f, Mixed)
    a = bt.run()["_strategy"]
    b = bt.run()["_strategy"]
    assert a.seen == b.seen and a.saved is not b.saved
    assert not a.m.valid[:2].any() and a.p.p.valid[0]
    with pytest.raises(IndicatorError, match="missing-input"):
        compute("ta.anchored_vwap", f)
    with pytest.raises(IndicatorError, match="missing-input"):
        compute("ta.mode", f, inputs={"unknown": "Close"})


def test_tr_wrapper_preserves_backend_rejected_input():
    from openbacktesting.indicators.volatility.true_range import compute as wrapped

    # 公开运行时已校验来源；适配器仍须保留后端拒绝输入时的空结果契约。
    # 这里直接调用适配器，避免把公共入口的 missing-input 当作算法返回值。
    prices = pd.Series([10.0])
    assert (
        wrapped(high=None, low=prices, close=prices, drift=1, talib=False, handle_na=False) is None
    )
