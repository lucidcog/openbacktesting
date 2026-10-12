"""Built-in indicator catalog, pure computation entry points, and bounded computation reuse."""

from __future__ import annotations

import json
from collections import OrderedDict
from concurrent.futures import Future
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from importlib.metadata import version
from threading import RLock
from uuid import uuid4

import numpy as np
import pandas as pd

from .common import SPECS, to_arrays
from .registry import execute, validate_backend
from .types import IndicatorCursor, IndicatorError, IndicatorHandle

DEFAULT_CACHE_BYTES = 64 * 1024 * 1024
_CATALOG = {spec.id: spec for spec in SPECS}
_COLUMNS = {"open_": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}


def catalog():
    """Return a tuple of all reviewed definitions, including deferred entries that cannot be called.

    Returns:
        tuple: Indicator definitions; check status before calling, and expect the count to vary with the reviewed catalog.
    """
    return tuple(_CATALOG.values())


def describe(indicator):
    """Look up an indicator definition by stable ID without computing it.

    Args:
        indicator: Full catalog ID, such as ta.ema.

    Returns:
        IndicatorSpec: Definition of parameter domains, outputs, status, and semantic version.

    Raises:
        IndicatorError: code is unknown-indicator when the ID does not exist.
    """
    try:
        return _CATALOG[indicator]
    except KeyError as error:
        raise IndicatorError("unknown-indicator", indicator, "Unregistered indicator") from error


class IndicatorCache:
    """The budget limits cache retention; active strategies' holdings are not bounded by this budget."""

    def __init__(self, budget=DEFAULT_CACHE_BYTES):
        if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
            raise ValueError("Cache budget must be a nonnegative integer")
        self.budget = budget
        self.bytes = 0
        self.hits = self.misses = 0
        self._entries = OrderedDict()
        self._pending = {}
        self._lock = RLock()

    def get(self, key, calculate):
        """Look up key in the cache or run calculate; coalesce concurrent identical keys, do not cache failures, and return read-only templates."""
        if not self.budget:
            self.misses += 1
            return calculate()
        with self._lock:
            if key in self._entries:
                self.hits += 1
                self._entries.move_to_end(key)
                return self._entries[key][0]
            if key in self._pending:
                future = self._pending[key]
                owner = False
            else:
                future = self._pending[key] = Future()
                self.misses += 1
                owner = True
        if not owner:
            return future.result()
        try:
            value = calculate()
            size = (
                value._values.nbytes
                + value._valid.nbytes
                + value._ready.nbytes
                + value._gating.nbytes
                + value._opts["index"].nbytes
            )
            with self._lock:
                if self.budget and size <= self.budget:
                    while self.bytes + size > self.budget:
                        _, (_, removed) = self._entries.popitem(last=False)
                        self.bytes -= removed
                    self._entries[key] = (value, size)
                    self.bytes += size
                future.set_result(value)
            return value
        except BaseException as error:
            future.set_exception(error)
            raise
        finally:
            with self._lock:
                del self._pending[key]

    def clear(self):
        """Clear retained entries and reset retained bytes to zero; do not revoke active result references."""
        with self._lock:
            self._entries.clear()
            self.bytes = 0


def _data_identity(frame):
    digest = sha256(pd.util.hash_pandas_object(frame, index=True).values.tobytes())
    digest.update(
        repr(
            (
                tuple(frame.columns),
                tuple(map(str, frame.dtypes)),
                str(frame.index.dtype),
                frame.index.name,
            )
        ).encode()
    )
    return digest.hexdigest()


def _prepare_inputs(spec, frame, inputs, cursor):
    if not isinstance(frame, pd.DataFrame) or not frame.index.is_unique:
        raise IndicatorError("index-mismatch", spec.id, "Input must be a DataFrame with a unique index")
    mapping = dict(inputs or {})
    if mapping.keys() - set(spec.inputs):
        raise IndicatorError("missing-input", spec.id, "Input mapping contains undeclared fields")
    columns = {}
    dtypes = {}
    defaults = dict(spec.input_defaults)
    for name in spec.inputs:
        source = mapping.get(name, defaults.get(name, _COLUMNS.get(name, name)))
        if isinstance(source, IndicatorHandle):
            if cursor is None or source._cursor is not cursor or source.ndim != 1:
                raise IndicatorError("index-mismatch", spec.id, "Indicator inputs must come from a single channel in this run")
            series = source.s.where(source.valid)
        else:
            if not isinstance(source, str) or source not in frame:
                raise IndicatorError("missing-input", spec.id, f"Missing input: {name}")
            series = frame[source]
        if not series.index.equals(frame.index):
            raise IndicatorError("index-mismatch", spec.id, "Input index does not match")
        if not pd.api.types.is_numeric_dtype(series.dtype):
            raise IndicatorError("missing-input", spec.id, f"{name} must be numeric")
        dtypes[name] = str(series.dtype)
        columns[name] = series.to_numpy(dtype=float, copy=False)
    prepared = pd.DataFrame(columns, index=frame.index, copy=True)
    prepared.attrs["input_dtypes"] = dtypes
    return prepared


def compute(
    indicator,
    frame,
    *,
    parameters=None,
    backend=None,
    inputs=None,
    cache=None,
    cursor=None,
    required_outputs=None,
):
    """Compute reviewed indicators in bulk on explicit market data and return read-only result handles.

    Args:
        indicator: Full catalog ID.
        frame: pandas DataFrame; index and inputs must satisfy the indicator contract.
        parameters: Parameter mapping; reject unknown keys, invalid types, and invalid relationships.
        backend: Backend identifier; None uses the catalog default without silent fallback.
        inputs: Mapping from indicator inputs to market-data column names or single channels from the same run.
        cache: Optional IndicatorCache; None recomputes each time.
        cursor: Internal framework run cursor; None for standalone computation.
        required_outputs: Canonical required output names; an empty list disables warmup gating.

    Returns:
        IndicatorHandle: Single- or multi-channel handle with valid/ready masks and provenance metadata.

    Raises:
        IndicatorError: Failure in ID, parameters, backend, inputs, outputs, or computation.
    """
    spec = describe(indicator)
    parameters = spec.normalize(dict(parameters or {}))
    backend = spec.default_backend if backend is None else backend
    binding = validate_backend(spec, backend)
    if spec.status != "available":
        raise IndicatorError("unavailable-indicator", indicator, spec.reason)
    required = spec.outputs if spec.required is None else spec.required
    required = tuple(required if required_outputs is None else required_outputs)
    if not set(required) <= set(spec.outputs):
        raise IndicatorError("output-contract", indicator, "Unknown required channel")
    data = _prepare_inputs(spec, frame, inputs, cursor)
    metadata = {
        "id": indicator,
        "semantic_version": spec.version,
        "implementation_version": binding.implementation_version,
        "parameters": parameters,
        "data_identity": _data_identity(data),
        "input_dtypes": data.attrs["input_dtypes"],
        "backend": backend,
        "versions": {name: version(name) for name in ("pandas-ta-classic", "pandas", "numpy")},
        "dtype": spec.dtype,
        "kind": spec.kind,
        "validity": spec.validity,
        "missing_policy": spec.missing_policy,
        "readiness": "history-and-finite-v1",
        "unit": spec.unit,
        "engine_version": version("openbacktesting"),
        "inputs": {
            name: (source.metadata | {"channel": source.name})
            if isinstance(source, IndicatorHandle)
            else source
            for name, source in (inputs or {}).items()
        },
        "fixed": dict(spec.fixed),
    }
    key = json.dumps(metadata, sort_keys=True)

    def calculate():
        try:
            result = execute(spec, {name: data[name] for name in spec.inputs}, parameters, backend)
        except IndicatorError:
            raise
        except Exception as error:
            raise IndicatorError(
                "calculation-failed", indicator, str(error), backend=backend
            ) from error
        values, valid = to_arrays(spec, result, data.index, parameters)
        ready = np.arange(len(data)) >= spec.history_required(parameters) - 1
        current_valid = np.isfinite(data.to_numpy()).all(axis=1)
        valid &= ready
        if spec.validity == "current-inputs":
            valid &= current_valid
        # Unready values are not used for trading; preserve native values for diagnostics rather than filling zeros to feign validity.
        if spec.dtype != "float64":
            values = np.nan_to_num(values).astype(spec.dtype)
        if len(spec.outputs) == 1:
            values, valid = values[0], valid[0]
        return IndicatorHandle(
            values,
            name=spec.outputs[0] if len(spec.outputs) == 1 else spec.outputs,
            index=data.index,
            valid=valid,
            metadata=metadata,
            ready=ready,
        )

    template = calculate() if cache is None else cache.get(key, calculate)
    handle = object.__new__(IndicatorHandle)
    handle.__dict__ = template.__dict__.copy()
    handle._metadata = deepcopy(template._metadata)
    handle._cursor = cursor or IndicatorCursor(len(frame), "complete")
    handle._set_required(spec.outputs.index(name) for name in required)
    handle._opts = template._opts.copy()
    handle._metadata["required_outputs"] = list(required)
    return handle


_OPTIMIZATION_CACHES = {}
_OPTIMIZATION_LOCK = RLock()


def optimization_cache(token, budget):
    """Reuse within a process; token is serializable, while caches and locks are excluded from task messages."""
    with _OPTIMIZATION_LOCK:
        if token not in _OPTIMIZATION_CACHES:
            _OPTIMIZATION_CACHES[token] = IndicatorCache(budget)
        return _OPTIMIZATION_CACHES[token]


@contextmanager
def optimization_scope(budget):
    """The parent process/thread releases in finally; child caches are released when the Pool owned by this run exits."""
    token = uuid4().hex
    optimization_cache(token, budget)
    try:
        yield token
    finally:
        with _OPTIMIZATION_LOCK:
            _OPTIMIZATION_CACHES.pop(token).clear()
