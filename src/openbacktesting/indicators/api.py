"""Lightweight adapter for method-style indicator entry points; strategies still handle computation and registration."""

from collections.abc import Callable, Mapping, Sequence

from .predicates import CrossPredicates
from .types import IndicatorError, IndicatorHandle

Source = str | IndicatorHandle
Inputs = Mapping[str, Source]


class IndicatorResult:
    """Read-only attribute container for multiple outputs; channel views are created only during initialization."""

    __slots__ = ("_channels", "_handle")

    def __init__(self, handle: IndicatorHandle):
        self._handle = handle
        self._channels = {name: handle[name] for name in handle.name}

    def __getitem__(self, name: str) -> IndicatorHandle:
        return self._channels[name]

    @property
    def ready(self):
        """Minimum-history mask shared by all outputs."""
        return self._handle.ready

    @property
    def valid(self):
        """Underlying validity masks for each channel; check the selected channel before trading."""
        return self._handle.valid

    @property
    def metadata(self):
        """Return an independent copy of the underlying handle's provenance metadata."""
        return self._handle.metadata

    @property
    def df(self):
        """Return a pandas DataFrame copy of the currently visible prefix of all channels."""
        return self._handle.df


class IndicatorNamespace(CrossPredicates):
    """Bind a registration callback to one strategy, avoiding an indicator-layer dependency on strategy implementations."""

    def __init__(self, register: Callable[..., IndicatorHandle]):
        self._register = register

    def _call(
        self,
        indicator: str,
        primary: str,
        source: Source | None,
        inputs: Inputs | None,
        backend: str | None,
        required_outputs: Sequence[str] | None,
        parameters: dict,
    ) -> IndicatorHandle:
        if source is not None:
            if inputs is not None:
                raise IndicatorError(
                    "invalid-parameter", indicator, "source and inputs cannot both be specified"
                )
            if not isinstance(source, (str, IndicatorHandle)):
                raise IndicatorError(
                    "missing-input", indicator, "source must be a column name or single-channel handle; select a channel from multi-output handles first"
                )
            inputs = {primary: source}
        return self._register(
            indicator,
            inputs=inputs,
            backend=backend,
            required_outputs=required_outputs,
            **parameters,
        )

    def _call_inputs(
        self,
        indicator: str,
        sources: dict[str, Source | None],
        inputs: Inputs | None,
        backend: str | None,
        required_outputs: Sequence[str] | None,
        parameters: dict,
    ) -> IndicatorHandle:
        bound = {name: source for name, source in sources.items() if source is not None}
        if bound and inputs is not None:
            raise IndicatorError("invalid-parameter", indicator, "Named inputs and inputs cannot both be specified")
        return self._register(
            indicator,
            inputs=bound if bound else inputs,
            backend=backend,
            required_outputs=required_outputs,
            **parameters,
        )
