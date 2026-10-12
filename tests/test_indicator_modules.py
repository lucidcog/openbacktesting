"""Independent acceptance of per-indicator files, migration baselines, and semantic adaptations."""

import base64
import hashlib
import inspect
import json
import pickle
from pathlib import Path

import numpy as np
import pytest
from test_indicator_catalog import AVAILABLE, catalog_data

from openbacktesting import indicators as public
from openbacktesting.indicators import runtime as indicators
from openbacktesting.indicators.methods import TechnicalAnalysis

BASELINE = json.loads(Path(__file__).with_name("indicator-package-baseline.json").read_text())


def digest(array):
    value = np.asarray(array).copy()
    if np.issubdtype(value.dtype, np.inexact):
        value[np.isnan(value)] = np.nan
    return hashlib.sha256(value.tobytes()).hexdigest()


@pytest.mark.parametrize(
    "spec",
    [s for s in AVAILABLE if s.id in BASELINE["results"] and s.version == "1"],
    ids=lambda spec: spec.id,
)
def test_pre_migration_values_masks_signatures(spec):
    expected = BASELINE["results"][spec.id]
    result = public.compute(spec.id, catalog_data())
    assert digest(result) == expected["values"]
    assert hashlib.sha256(result.valid.tobytes()).hexdigest() == expected["valid"]
    assert hashlib.sha256(result.ready.tobytes()).hexdigest() == expected["ready"]
    assert str(inspect.signature(getattr(TechnicalAnalysis, spec.source))) == expected["signature"]
    actual = result.metadata
    actual.pop("implementation_version", None)
    previous = expected["metadata"].copy()
    # Remove the dispatch switch without rewriting fixed algorithm, numerical, or provenance baselines.
    previous.pop("warmup")
    assert "warmup" not in actual
    # Allow only safe options explicitly defined by the catalog; compare all other metadata.
    additions = {
        "ta.ema": {"offset": 0},
        "ta.sma": {"offset": 0},
        "ta.macd": {"offset": 0, "asmode": False, "signal_indicators": False},
    }
    previous["fixed"] |= additions.get(spec.id, {})
    previous.update(kind="indicator", validity="current-inputs", engine_version="0.2.0")
    assert actual == previous


def test_old_pickle_and_public_type_identity():
    from openbacktesting.indicator_api import IndicatorResult as OldResult
    from openbacktesting.indicator_methods import MacdResult as OldMacd
    from openbacktesting.indicator_types import IndicatorHandle as OldHandle
    from openbacktesting.indicators.api import IndicatorResult
    from openbacktesting.indicators.methods import MacdResult
    from openbacktesting.indicators.types import IndicatorHandle

    assert (OldResult, OldMacd, OldHandle) == (IndicatorResult, MacdResult, IndicatorHandle)
    payload = base64.b64decode(BASELINE["pickle_base64"])
    assert hashlib.sha256(payload).hexdigest() == BASELINE["pickle_sha256"]
    restored = pickle.loads(payload)
    assert type(restored["handle"]) is IndicatorHandle
    assert type(restored["result"]) is MacdResult
    assert digest(restored["handle"]) == BASELINE["results"]["ta.macd"]["values"]
    assert (
        hashlib.sha256(restored["handle"].valid.tobytes()).hexdigest()
        == (BASELINE["results"]["ta.macd"]["valid"])
    )
    assert restored["result"].line is restored["result"].macd
    assert restored["result"].histogram is restored["histogram"]
    assert restored["histogram"]._cursor is restored["cursor"]
    with pytest.raises(ValueError):
        restored["handle"]._values.setflags(write=True)
    restored["cursor"].length = 50
    assert len(restored["histogram"]) == 50
    assert public.compute is indicators.compute


def test_every_indicator_owns_one_file_and_binding():
    from openbacktesting.indicators import registry

    root = Path(inspect.getfile(public)).parent
    expected = {root / spec.category / f"{spec.source}.py" for spec in AVAILABLE}
    actual = {path for path in root.glob("*/*.py") if path.name != "__init__.py"}
    assert actual == expected and len(actual) == 244
    assert not (root / "backends").exists()
    assert {name for name in vars(TechnicalAnalysis) if not name.startswith("_")} == {
        spec.source for spec in AVAILABLE
    }
    for (indicator, _backend), binding in registry.BINDINGS.items():
        spec = indicators.describe(indicator)
        assert Path(inspect.getfile(binding.compute)) == root / spec.category / f"{spec.source}.py"
    assert len(registry.BINDINGS) == 245


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "unknown",
        "backend",
        "wrong_backend",
        "missing",
        "signature",
        "positional",
        "default",
        "module",
        "version",
        "empty_version",
    ],
)
def test_registry_rejects_incomplete_or_ambiguous_bindings(mutation):
    from openbacktesting.indicators.registry import ENTRIES, SPECS, build_bindings

    entries = list(ENTRIES)
    row = list(entries[0])
    if mutation == "duplicate":
        entries.append(entries[0])
    elif mutation == "unknown":
        row[0] = "ta.unknown"
    elif mutation == "backend":
        row[1] = "other"
    elif mutation == "wrong_backend":
        row[1] = "pandas.sma"
    elif mutation == "missing":
        entries.pop(0)
    elif mutation in {"signature", "positional", "default", "module"}:
        original = row[2]
        params = inspect.signature(original).parameters
        parameters = list(params.values())
        if mutation == "signature":
            parameters = [inspect.Parameter("unknown", inspect.Parameter.KEYWORD_ONLY)]
        elif mutation == "positional":
            parameters = [
                p.replace(kind=inspect.Parameter.POSITIONAL_OR_KEYWORD) for p in parameters
            ]
        elif mutation == "default":
            parameters = [p.replace(default=None) for p in parameters]

        def fake(**kwargs):
            return None

        fake.__signature__ = inspect.Signature(parameters)
        fake.__module__ = "wrong" if mutation == "module" else original.__module__
        row[2] = fake
    elif mutation == "version":
        row[3] = 1
    else:
        row[3] = ""
    if mutation not in {"duplicate", "missing"}:
        entries[0] = tuple(row)
    with pytest.raises(ValueError):
        build_bindings(entries, SPECS)


@pytest.mark.parametrize(
    "mutation", ["swap", "missing", "extra", "duplicate", "renamed", "array", "index"]
)
def test_macd_maps_names_and_rejects_bad_outputs(monkeypatch, mutation):
    import pandas as pd

    from openbacktesting.indicators.momentum import macd
    from openbacktesting.indicators.types import IndicatorError

    data = catalog_data()
    expected = public.compute("ta.macd", data)
    raw = macd._calculate(data.Close, fast=12, slow=26, signal=9, talib=False)
    if mutation == "swap":
        raw = raw.iloc[:, ::-1]
    elif mutation == "missing":
        raw = raw.iloc[:, :2]
    elif mutation == "extra":
        raw = raw.assign(extra=0.0)
    elif mutation == "duplicate":
        raw.columns = [raw.columns[0]] * 3
    elif mutation == "renamed":
        raw.columns = ["a", "b", "c"]
    elif mutation == "array":
        raw = raw.to_numpy()
    else:
        raw.index = pd.RangeIndex(len(raw))
    monkeypatch.setattr(macd, "_calculate", lambda **kwargs: raw)
    if mutation == "swap":
        np.testing.assert_allclose(public.compute("ta.macd", data), expected, equal_nan=True)
    else:
        code = "index-mismatch" if mutation == "index" else "output-contract"
        with pytest.raises(IndicatorError) as error:
            public.compute("ta.macd", data)
        assert error.value.code == code
        assert error.value.indicator == "ta.macd"


def test_common_contracts_and_stable_error_identity(monkeypatch):
    import pandas as pd

    from openbacktesting.indicators import common
    from openbacktesting.indicators.overlap import sma
    from openbacktesting.indicators.types import IndicatorError

    data = catalog_data()
    with pytest.raises(IndicatorError, match="single-channel Series is required"):
        common.named_series(pd.DataFrame({"sma": [1.0]}), "ta.sma", "sma")
    spec = public.describe("ta.sma")
    with pytest.raises(IndicatorError, match="name"):
        common.to_arrays(spec, pd.Series([1.0], name="wrong"), pd.RangeIndex(1), {"length": 10})

    class MalformedSeries(pd.Series):
        def to_numpy(self, dtype=None):
            return np.zeros((2, len(self)))

    with pytest.raises(IndicatorError, match="Invalid output shape"):
        common.to_arrays(spec, MalformedSeries([1.0], name="sma"), pd.RangeIndex(1), {"length": 10})
    failure = IndicatorError("output-contract", "ta.sma", "sample")

    def fail(**kwargs):
        raise failure

    monkeypatch.setattr(sma, "_calculate", fail)
    with pytest.raises(IndicatorError) as caught:
        public.compute("ta.sma", data)
    assert caught.value is failure


def test_implementation_version_and_missing_binding(monkeypatch):
    from dataclasses import replace

    from openbacktesting.indicators import registry
    from openbacktesting.indicators.types import IndicatorError

    cache = public.IndicatorCache()
    data = catalog_data()
    first = public.compute("ta.sma", data, cache=cache)
    key = ("ta.sma", registry.NATIVE)
    monkeypatch.setitem(
        registry.BINDINGS, key, replace(registry.BINDINGS[key], implementation_version="2")
    )
    second = public.compute("ta.sma", data, cache=cache)
    assert cache.misses == 2
    assert first.metadata["implementation_version"] == "1"
    assert second.metadata["implementation_version"] == "2"
    np.testing.assert_allclose(first, second, equal_nan=True)
    monkeypatch.delitem(registry.BINDINGS, key)
    with pytest.raises(IndicatorError, match="backend-unavailable"):
        public.compute("ta.sma", data)


@pytest.mark.parametrize(
    "aliases", [(("x", "missing"),), (("macd", "macd"),), (("x", "macd"), ("x", "signal"))]
)
def test_alias_contract_rejects_invalid_or_duplicate_names(aliases):
    from dataclasses import replace

    with pytest.raises(ValueError, match="alias"):
        replace(public.describe("ta.macd"), aliases=aliases)
