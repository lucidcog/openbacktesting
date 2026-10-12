"""Per-entry acceptance against fixed artifacts; catalog changes require review rather than automatically exposing APIs."""

import builtins
import json
from importlib.resources import files

import numpy as np
import pandas as pd
import pandas_ta_classic as ta
import pytest

from openbacktesting.indicator_types import IndicatorError
from openbacktesting.indicators import runtime as indicators

AVAILABLE = [spec for spec in indicators.catalog() if spec.status == "available"]
REFERENCE_AVAILABLE = [
    spec
    for spec in AVAILABLE
    if spec.kind == "indicator"
    and spec.default_backend == "pandas-ta-classic.native"
    and spec.id not in {"ta.squeeze", "ta.squeeze_pro"}
]


def catalog_data(n=512):
    rng = np.random.default_rng(42)
    close = 100 + rng.normal(0, 1, n).cumsum()
    data = pd.DataFrame(
        {
            "Close": close,
            "High": close + rng.uniform(0.1, 2, n),
            "Low": close - rng.uniform(0.1, 2, n),
            "Open": close + 0.1,
            "Volume": rng.integers(100, 5000, n).astype(float),
        },
        index=pd.date_range("2020-01-01", periods=n, freq="min", tz="UTC"),
    )
    data["source"] = data.Close
    data["benchmark"] = close * 1.2 + rng.normal(0, 0.1, n)
    data["periods"] = 10.0
    data["fast"] = data.Close.rolling(3).mean()
    data["slow"] = data.Close.rolling(10).mean()
    data["trend"] = (data.Close.diff() > 0).astype(float)
    data["signal"] = data.Close.pct_change() * 100
    data["left"] = data.Close
    data["right"] = data.Close.rolling(4).mean()
    data["condition"] = (np.arange(n) % 7 == 0).astype(float)
    data["anchor"] = (np.arange(n) % 20 == 0).astype(float)
    return data


def test_installed_inventory_and_reviewed_definitions():
    rows = json.loads(files("openbacktesting.indicators").joinpath("catalog.json").read_text())[
        "entries"
    ]
    expected = {(category, name) for category, names in ta.Category.items() for name in names}
    actual = {(row["category"], row["source"]) for row in rows}
    assert expected <= actual
    assert len(actual) == 247
    assert len([r for r in rows if r["status"] == "available"]) == 244
    assert len(rows) == len(indicators.catalog())
    assert {row["status"] for row in rows} <= {
        "available",
        "unsupported",
        "deferred-pattern",
        "research-only",
        "non-series",
    }
    for spec in indicators.catalog():
        if spec.status != "available":
            assert spec.reason
            with pytest.raises(IndicatorError, match="unavailable-indicator"):
                indicators.compute(spec.id, catalog_data())


@pytest.mark.parametrize("spec", REFERENCE_AVAILABLE, ids=lambda spec: spec.id)
def test_catalog_native_values_prefixes_short_history_and_talib_sentinel(spec, monkeypatch):
    original = builtins.__import__

    def reject(module, *args, **kwargs):
        if module == "talib":
            pytest.fail(f"{spec.id} TA-Lib was invoked")
        return original(module, *args, **kwargs)

    monkeypatch.setitem(ta.Imports, "talib", True)
    monkeypatch.setattr(builtins, "__import__", reject)
    data = catalog_data()
    actual = indicators.compute(spec.id, data)
    assert actual.shape[-1] == len(data)
    assert actual.s.index.equals(data.index)
    params = spec.normalize({})
    inputs = {name: data[indicators._COLUMNS.get(name, name)] for name in spec.inputs}
    reference = getattr(ta, spec.source)(**inputs, **(params | dict(spec.fixed) | {"talib": False}))
    expected = reference.to_numpy().T
    if len(spec.outputs) == 1:
        expected = expected.reshape(-1)
    np.testing.assert_allclose(actual, expected, equal_nan=True, rtol=1e-12)
    for n in [200, 333, 450]:
        prefix = indicators.compute(spec.id, data.iloc[:n])
        np.testing.assert_allclose(np.asarray(actual)[..., :n], prefix, equal_nan=True)
        np.testing.assert_array_equal(actual.valid[..., :n], prefix.valid)
        np.testing.assert_array_equal(actual.ready[:n], prefix.ready)
    for n in [0, 1, 2, 5]:
        short = indicators.compute(spec.id, data.iloc[:n])
        assert short.shape[-1] == n
        assert short.valid.shape == short.shape
    constant = data.copy()
    constant.loc[:, ["Open", "High", "Low", "Close"]] = 100.0
    constant.loc[:, "Volume"] = 1000.0
    flat = indicators.compute(spec.id, constant)
    assert not (flat.valid & ~np.isfinite(flat)).any()
    gap = data.copy()
    gap.iloc[256, gap.columns.get_indexer(["Open", "High", "Low", "Close", "Volume"])] = np.nan
    gapped = indicators.compute(spec.id, gap)
    if set(spec.inputs) & set(indicators._COLUMNS):
        assert not gapped.valid[..., 256].any()


@pytest.mark.parametrize("spec", AVAILABLE, ids=lambda spec: spec.id)
def test_catalog_parameters_reject_unknown_and_bool_lengths(spec):
    with pytest.raises(IndicatorError, match="invalid-parameter"):
        indicators.compute(spec.id, catalog_data(), parameters={"talib": True})
    for name, rule in spec.parameters:
        if rule.kind in ("int", "float"):
            with pytest.raises(IndicatorError, match="invalid-parameter"):
                spec.normalize({name: True})


@pytest.mark.parametrize("spec", REFERENCE_AVAILABLE, ids=lambda spec: spec.id)
def test_supported_parameter_boundaries_and_enums_are_causal(spec):
    data = catalog_data()
    for name, rule in spec.parameters:
        # test_local_builtin_indicators verifies nondefault semantics of new local parameters with hand calculations and prefix checks;
        # Upstream parameters with the same name are absent or mean shift and cannot provide reference values for these branches.
        if (spec.id, name) in {
            ("ta.true_range", "handle_na"),
            ("ta.kc", "use_true_range"),
            ("ta.alma", "floor"),
            ("ta.linreg", "offset"),
        }:
            continue
        if rule.choices:
            values = rule.choices
        elif rule.kind == "bool":
            values = [not rule.default]
        elif rule.minimum is not None:
            values = [int(rule.minimum) if rule.kind == "int" else rule.minimum]
        else:
            values = [rule.default]
        for value in values:
            try:
                spec.normalize({name: value})
            except IndicatorError:
                continue  # A single-parameter boundary may violate independently tested cross-parameter constraints.
            full = indicators.compute(spec.id, data, parameters={name: value})
            params = spec.normalize({name: value})
            inputs = {key: data[indicators._COLUMNS.get(key, key)] for key in spec.inputs}
            reference = getattr(ta, spec.source)(
                **inputs, **(params | dict(spec.fixed) | {"talib": False})
            )
            expected = reference.to_numpy(dtype=float).T
            if len(spec.outputs) == 1:
                expected = expected.reshape(-1)
            np.testing.assert_allclose(full, expected, equal_nan=True, rtol=1e-12)
            prefix = indicators.compute(spec.id, data.iloc[:333], parameters={name: value})
            np.testing.assert_allclose(np.asarray(full)[..., :333], prefix, equal_nan=True)
            np.testing.assert_array_equal(full.valid[..., :333], prefix.valid)


@pytest.mark.parametrize("name", ["ad", "adosc", "cmf", "psl"])
def test_optional_open_does_not_silently_select_a_different_formula(name):
    data = catalog_data()
    full = indicators.compute("ta." + name, data)
    changed = data.assign(Open=data.Open + 50)
    same = indicators.compute("ta." + name, changed)
    np.testing.assert_allclose(full, same, equal_nan=True)
    spec = indicators.describe("ta." + name)
    raw = getattr(ta, name)(
        **{key: data[indicators._COLUMNS[key]] for key in spec.inputs}, talib=False
    )
    np.testing.assert_allclose(full, raw, equal_nan=True)
