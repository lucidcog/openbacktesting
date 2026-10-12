"""Provider-independent indicator definitions, immutable results, and cursor views."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import isfinite

import numpy as np
import pandas as pd
from numpy.lib.mixins import NDArrayOperatorsMixin


class IndicatorError(ValueError):
    """Stable error categories; detail is not a programmatic dispatch interface."""

    def __init__(self, code, indicator, detail, *, backend=None, parameter=None):
        self.code = code
        self.indicator = indicator
        self.backend = backend
        self.parameter = parameter
        super().__init__(f"{code}: {indicator}: {detail}")


def immutable(values, dtype=None):
    """Backed by immutable bytes, so setflags cannot restore write access."""
    array = np.asarray(values, dtype=dtype)
    if array.dtype.hasobject:
        raise ValueError("Indicator arrays do not accept object dtype")
    return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)


@dataclass
class IndicatorCursor:
    length: int
    phase: str = "init"


class IndicatorHandle(NDArrayOperatorsMixin):
    """Time is the final dimension; all derived views apply cursors and selectors only when read."""

    def __init__(
        self,
        values,
        *,
        name,
        index,
        cursor=None,
        valid=None,
        required=None,
        metadata=None,
        ready=None,
    ):
        self._values = immutable(values)
        self.name = name
        self._opts = {"index": index.copy(deep=True)}
        self._cursor = cursor or IndicatorCursor(self._values.shape[-1], "complete")
        self._selectors = ()
        self._valid = immutable(np.isfinite(self._values) if valid is None else valid, bool)
        self._required = (
            tuple(range(np.atleast_2d(self._values).shape[0]))
            if required is None
            else tuple(required)
        )
        self._metadata = deepcopy(metadata or {})
        self._ready = immutable(
            np.ones(self._values.shape[-1], dtype=bool) if ready is None else ready, bool
        )
        self._set_required(self._required)

    def _view(self):
        value = self._values[..., : self._cursor.length]
        for selector in self._selectors:
            value = value[selector]
        return value

    def _index(self):
        indices = np.broadcast_to(
            np.arange(self._cursor.length), self._values.shape[:-1] + (self._cursor.length,)
        )
        for selector in self._selectors:
            indices = indices[selector]
        return self._opts["index"][np.atleast_2d(indices)[0]]

    def __array__(self, dtype=None, copy=None):
        # Conversion saves only the currently visible snapshot; .base does not expose the complete future array.
        if copy is False:
            raise ValueError("Indicator conversion requires an isolated snapshot; copy=False is not allowed")
        if copy is True:
            return np.array(self._view(), dtype=dtype, copy=True)
        return immutable(self._view(), dtype)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if kwargs.get("out") is not None or method == "at":
            raise TypeError("Indicators are read-only; copy to an array before in-place operations")
        values = [
            value._view() if isinstance(value, IndicatorHandle) else value for value in inputs
        ]
        return getattr(ufunc, method)(*values, **kwargs)

    def __getitem__(self, key):
        if isinstance(key, str):
            names = [self.name] if isinstance(self.name, str) else list(self.name)
            if key not in names:
                raise KeyError(key)
            key = names.index(key) if self.ndim == 2 else slice(None)
        value = self._view()[key]
        if not isinstance(value, np.ndarray):
            return value
        result = object.__new__(type(self))
        result.__dict__ = self.__dict__.copy()
        result._selectors = self._selectors + (key,)
        if self.ndim == 2 and isinstance(key, (int, np.integer)):
            result.name = self.name[key] if not isinstance(self.name, str) else self.name
        return result

    def __len__(self):
        return len(self._view())

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __bool__(self):
        return bool(self[-1])

    def __float__(self):
        return float(self[-1])

    @property
    def shape(self):
        """Shape of the currently visible prefix; time is the last axis for multiple outputs."""
        return self._view().shape

    @property
    def ndim(self):
        """Output dimensions: 1 for a single channel, 2 for multiple channels."""
        return self._view().ndim

    @property
    def dtype(self):
        """Data type of the underlying read-only numeric buffer."""
        return self._values.dtype

    @property
    def s(self):
        """pandas Series copy of the first channel's current prefix; saved copies do not grow with the cursor."""
        return pd.Series(
            np.atleast_2d(np.asarray(self))[0].copy(), index=self._index(), name=self.name
        )

    @property
    def df(self):
        """pandas DataFrame copy of all channels' current prefixes."""
        value = np.atleast_2d(np.asarray(self))
        names = self.name if isinstance(self.name, (list, tuple)) else [self.name] * len(value)
        return pd.DataFrame(value.T.copy(), index=self._index(), columns=names)

    def copy(self):
        """Return a writable NumPy copy of the current prefix that no longer follows the cursor."""
        return np.array(self, copy=True)

    def astype(self, dtype):
        """Convert the current prefix to a NumPy array snapshot with dtype; do not retain a dynamic cursor."""
        return np.asarray(self, dtype=dtype)

    @property
    def valid(self):
        """Read-only validity masks for each channel's current prefix; False does not mean numeric zero."""
        value = self._valid[..., : self._cursor.length]
        for selector in self._selectors:
            value = value[selector]
        return immutable(value)

    @property
    def ready(self):
        """Read-only mask indicating whether the current prefix meets minimum-history conditions."""
        return immutable(self._ready[: self._cursor.length])

    @property
    def metadata(self):
        """Return a deep copy of provenance metadata; modifications do not affect the registered result."""
        return deepcopy(self._metadata)

    def _set_required(self, required):
        self._required = tuple(required)
        self._gating = immutable(
            self._ready & np.atleast_2d(self._valid)[list(self._required)].all(axis=0)
        )

    def ready_at(self, bar):
        """Query readiness of required outputs and minimum-history conditions; does not control strategy callbacks."""
        return bool(self._gating[bar])

    def first_ready(self):
        """Return the earliest ready position for required outputs, or total length if never ready; does not control callbacks."""
        positions = np.flatnonzero(self._gating)
        return int(positions[0]) if positions.size else len(self._gating)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._values = immutable(self._values)
        self._valid = immutable(self._valid, bool)
        self._ready = immutable(self._ready, bool)
        self._gating = immutable(self._gating, bool)


@dataclass(frozen=True)
class Parameter:
    """Indicator parameter definition: default/kind define default value and type; minimum/maximum/choices constrain allowed values."""

    default: object
    kind: str
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple = ()

    def normalize(self, value, indicator, name):
        """Validate value type, bounds, and choices and convert to a native type; failures raise IndicatorError, located by indicator/name."""
        types = {
            "int": (int, np.integer),
            "float": (int, float, np.integer, np.floating),
            "bool": (bool,),
            "str": (str,),
        }
        valid = isinstance(value, types[self.kind])
        if self.kind in ("int", "float"):
            valid = valid and not isinstance(value, (bool, np.bool_))
            if valid:
                try:
                    valid = isfinite(value)
                except OverflowError:
                    valid = False
        if valid and self.minimum is not None:
            valid = value >= self.minimum
        if valid and self.maximum is not None:
            valid = value <= self.maximum
        if valid and self.choices:
            valid = value in self.choices
        if not valid:
            raise IndicatorError(
                "invalid-parameter", indicator, f"{name}: {value!r}", parameter=name
            )
        return {"int": int, "float": float, "bool": bool, "str": str}[self.kind](value)


@dataclass(frozen=True)
class IndicatorSpec:
    """Reviewed indicator definition containing identity, inputs/outputs, parameter domains, backends, validity, and history requirements."""

    id: str
    source: str
    category: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    parameters: tuple[tuple[str, Parameter], ...] = ()
    version: str = "1"
    status: str = "available"
    reason: str = ""
    required: tuple[str, ...] | None = None
    fixed: tuple[tuple[str, object], ...] = ()

    minimum: int = 1
    windows: tuple[str, ...] = ()
    dtype: str = "float64"
    unit: str = "native"
    missing_policy: str = "native-v1"
    causal: bool = True

    aliases: tuple[tuple[str, str], ...] = ()
    history_sum: tuple = ()
    history_offset: int = 0
    kind: str = "indicator"
    input_args: tuple[str, ...] = ()
    input_defaults: tuple[tuple[str, str], ...] = ()
    default_backend: str = "pandas-ta-classic.native"
    validity: str = "current-inputs"

    def history_required(self, parameters):
        """Calculate minimum history length from normalized parameters; this does not imply every output is valid."""
        return max(
            [
                self.minimum,
                *(parameters[name] for name in self.windows),
                self.history_offset
                + sum(parameters[name] * coefficient for name, coefficient in self.history_sum),
            ]
        )

    def __post_init__(self):
        if not self.id or not self.outputs or len(set(self.outputs)) != len(self.outputs):
            raise ValueError("Indicator identity and unique outputs must not be empty")
        aliases = [name for name, _ in self.aliases]
        if len(set(aliases)) != len(aliases) or any(
            name in self.outputs or target not in self.outputs for name, target in self.aliases
        ):
            raise ValueError("Duplicate output aliases or invalid targets")
        if self.kind not in ("indicator", "utility", "pattern") or self.validity not in (
            "current-inputs",
            "output",
        ):
            raise ValueError("Unknown indicator kind or validity policy")
        if len(set(self.input_args)) != len(self.input_args) or not set(self.input_args) <= set(
            self.inputs
        ):
            raise ValueError("Public input parameters must be unique and declared")
        defaults = dict(self.input_defaults)
        if len(defaults) != len(self.input_defaults) or not defaults.keys() <= set(self.inputs):
            raise ValueError("Default inputs must be unique and declared")
        names = [name for name, _ in self.parameters]
        if len(set(names)) != len(names) or set(names) & {"inputs", "backend", "required_outputs"}:
            raise ValueError("Duplicate parameters or parameters reserved for execution options")
        if self.required is not None and not set(self.required) <= set(self.outputs):
            raise ValueError("Required outputs are not declared in the definition")

    def normalize(self, parameters):
        """Validate the parameters mapping, fill catalog defaults, and check parameter relationships; invalid values raise IndicatorError."""
        definitions = dict(self.parameters)
        unknown = parameters.keys() - definitions.keys()
        if unknown:
            raise IndicatorError("invalid-parameter", self.id, f"Unknown parameter: {sorted(unknown)}")
        values = {
            name: rule.normalize(parameters.get(name, rule.default), self.id, name)
            for name, rule in self.parameters
        }
        if "fast" in values and "slow" in values and values["fast"] >= values["slow"]:
            raise IndicatorError("invalid-parameter", self.id, "fast must be less than slow")
        if "ddof" in values and "length" in values and values["ddof"] >= values["length"]:
            raise IndicatorError("invalid-parameter", self.id, "ddof must be less than length")
        for lower, upper in (("minperiod", "maxperiod"), ("slowlimit", "fastlimit")):
            if lower in values and upper in values and values[lower] >= values[upper]:
                raise IndicatorError("invalid-parameter", self.id, f"{lower} must be less than {upper}")
        if "kc_scalar_wide" in values and not (
            values["kc_scalar_wide"] > values["kc_scalar_normal"] > values["kc_scalar_narrow"]
        ):
            raise IndicatorError(
                "invalid-parameter", self.id, "KC coefficients must satisfy wide > normal > narrow"
            )
        if self.id == "ta.frama" and values["length"] % 2:
            raise IndicatorError("invalid-parameter", self.id, "length must be even")
        return values
