"""Consume successfully loaded strategy modules; discovery needs no data, and the host injects chart context for execution."""

from collections.abc import Mapping
from dataclasses import asdict
from importlib.metadata import version
from inspect import isabstract

import pandas as pd

from openbacktesting.broker.instrument import InstrumentSpec
from openbacktesting.data.context import DataContext
from openbacktesting.indicators.runtime import DEFAULT_CACHE_BYTES
from openbacktesting.logs import RunLogs
from openbacktesting.optimizer.query import ExperimentResult
from openbacktesting.plotting.types import PlottingLimits
from openbacktesting.simulation.collection import DEFAULT_COLLECTION, CollectionPolicy
from openbacktesting.simulation.core import Backtest
from openbacktesting.strategy.base import Strategy
from openbacktesting.strategy.declaration import declaration
from openbacktesting.strategy.inputs import describe as describe_inputs
from openbacktesting.strategy.inputs import resolve_request


def discover(namespace: Mapping) -> type[Strategy]:
    """Discover the single concrete strategy directly decorated in this module; deduplicate aliases and exclude imported and inherited entry points.

    Args:
        namespace: Successfully loaded module namespace containing a nonempty string __name__.

    Returns:
        type[Strategy]: Original strategy class, without instance construction.

    Raises:
        TypeError: Invalid namespace or declaration.
        ValueError: No entry point or multiple entry points.
    """
    if not isinstance(namespace, Mapping):
        raise TypeError("namespace must be a module mapping")
    name = namespace.get("__name__")
    if not isinstance(name, str) or not name:
        raise TypeError("namespace must contain a nonempty __name__")
    candidates = {}
    for value in namespace.values():
        if (
            isinstance(value, type)
            and issubclass(value, Strategy)
            and value.__module__ == name
            and not isabstract(value)
            and declaration(value) is not None
        ):
            candidates[id(value)] = value
    if len(candidates) != 1:
        names = sorted(f"{cls.__module__}:{cls.__qualname__}" for cls in candidates.values())
        raise ValueError(f"The module must contain exactly one @backtest strategy; candidates: {names}")
    return next(iter(candidates.values()))


def describe(namespace: Mapping) -> dict:
    """Export inputs and complete default backtest settings without market data or executing the strategy lifecycle.

    The returned backtest description is independent of input schemaHash; modifying copies does not alter class declarations.
    """
    cls = discover(namespace)
    settings = declaration(cls)
    return describe_inputs(cls) | {
        "backtest": {"schemaVersion": 2, "settings": settings.snapshot()}
    }


def run(
    namespace: Mapping,
    request: Mapping | None = None,
    *,
    data: pd.DataFrame,
    context: DataContext,
    instrument: InstrumentSpec,
    settings: Mapping | None = None,
    options: Mapping | None = None,
    logs: RunLogs | None = None,
) -> pd.Series:
    """Run a new session for this chart and return existing results plus backtest_snapshot.

    Args:
        namespace: Module successfully loaded by the host for this run; bt-only exports are no longer accepted.
        request: Existing title-based input request; None uses defaults.
        data: Current chart OHLC with a timezone-aware DatetimeIndex.
        context: Actual timeframe and shared timezone for charts, strategy calendars, and statistics.
            Convert the internal index before strategy construction, preserving inputs and absolute instants without resampling.
            Changing timezone requires a new run; local-time conditions and statistics grouped by day may change.
        instrument: Chart instrument specifications, without inference from market data.
        settings: Sparse overrides of flat settings; enum fields accept corresponding members or exact strings.
            Changing types requires supplying a value too; default_qty_value=None clears the default quantity.
        options: cache budget, plotting, and plotting_limits are host runtime options.
        logs: Optional host log session; get_logs works after success or exceptions, and sequential reuse clears old records.

    No source loading, cached old instances, or declaration changes; exceptions propagate unchanged.
    """
    if logs is not None and not isinstance(logs, RunLogs):
        raise TypeError("logs must be RunLogs or None")
    session = RunLogs() if logs is None else logs
    with session._capture():
        return _run(namespace, request, data, context, instrument, settings, options, session)


def _run(
    namespace,
    request,
    data,
    context,
    instrument,
    settings,
    options,
    session,
    collection=DEFAULT_COLLECTION,
):
    cls = discover(namespace)
    resolved = declaration(cls).resolve(settings)
    if not isinstance(context, DataContext):
        raise TypeError("context must be DataContext")
    if not isinstance(instrument, InstrumentSpec):
        raise TypeError("instrument must be InstrumentSpec")
    if options is None:
        options = {}
    if not isinstance(options, Mapping):
        raise TypeError("options must be a mapping or None")
    defaults = {
        "indicator_cache_bytes": DEFAULT_CACHE_BYTES,
        "plotting": True,
        "plotting_limits": PlottingLimits(),
    }
    unknown = set(options).difference(defaults)
    if unknown:
        raise ValueError(f"Unknown runtime option: {list(unknown)!r}")
    effective_options = defaults | dict(options)
    if effective_options["plotting_limits"] is None:
        effective_options["plotting_limits"] = PlottingLimits()
    # Digest and value errors must surface before constructing any strategy, preserving existing title-based entry semantics.
    if request is not None:
        resolve_request(cls, request)
    bt = Backtest(
        data,
        cls,
        context=context,
        instrument=instrument,
        _collection=collection,
        **resolved.kwargs(),
        **effective_options,
    )
    try:
        result = bt.run() if request is None else bt.run_inputs(request)
    finally:
        session._collector = bt._log_collector
    result.attrs["backtest_snapshot"] = {
        "schemaVersion": 2,
        "strategy": {"module": cls.__module__, "qualname": cls.__qualname__},
        "settings": resolved.snapshot(),
        "context": context.snapshot(),
        "instrument": asdict(instrument),
        "options": effective_options
        | {"plotting_limits": asdict(effective_options["plotting_limits"])},
        "engineVersion": version("openbacktesting"),
    }
    from openbacktesting.portfolio.snapshot import refresh_snapshot

    refresh_snapshot(result)
    return result


def optimize(
    namespace: Mapping,
    search: Mapping,
    *,
    path,
    identity,
    data: pd.DataFrame,
    context: DataContext,
    instrument: InstrumentSpec,
    request=None,
    settings=None,
    constraint=None,
    constraint_id=None,
    cancel=None,
    on_progress=None,
) -> ExperimentResult:
    """Exhaustively search selected inputs sequentially, committing each complete Portfolio to a new local result database.

    Unselected values come from the current request; retain only Portfolio without collecting logs/plotting.
    identity is a host-supplied ExecutionIdentity; the framework computes data/configuration identities.
    constraint uses complete wire values and requires constraint_id; cancel is a no-argument callable.
    Return a read-only ExperimentResult; record strategy-trial failures and continue, but stop on storage failures.
    """
    return _optimize(
        namespace,
        search,
        path,
        identity,
        data,
        context,
        instrument,
        request,
        settings,
        constraint,
        constraint_id,
        cancel,
        on_progress,
        None,
    )


def resume_optimization(
    namespace: Mapping,
    *,
    path,
    experiment_id: str,
    identity,
    data: pd.DataFrame,
    context: DataContext,
    instrument: InstrumentSpec,
    request=None,
    settings=None,
    constraint=None,
    constraint_id=None,
    cancel=None,
    on_progress=None,
) -> ExperimentResult:
    """Resume unfinished trials after checking current declarations, inputs, and execution identity; failed trials are not automatically retried."""
    from openbacktesting.optimizer.models import Range, Values
    from openbacktesting.optimizer.query import open_result

    source = open_result(path, experiment_id).info()["plan"]
    search = {}
    for dimension in source["dimensions"]:
        expression = dimension["expression"]
        search[dimension["title"]] = (
            Range(**expression["range"]) if "range" in expression else Values(expression["values"])
        )
    return _optimize(
        namespace,
        search,
        path,
        identity,
        data,
        context,
        instrument,
        request,
        settings,
        constraint,
        constraint_id,
        cancel,
        on_progress,
        experiment_id,
    )


def _optimize(
    namespace,
    search,
    path,
    identity,
    data,
    context,
    instrument,
    request,
    settings,
    constraint,
    constraint_id,
    cancel,
    on_progress,
    experiment_id,
):
    from copy import deepcopy

    from openbacktesting.optimizer.identity import execution_identity
    from openbacktesting.optimizer.models import _ExportError
    from openbacktesting.optimizer.plan import plan
    from openbacktesting.optimizer.runner import execute
    from openbacktesting.portfolio.snapshot import export_result

    cls = discover(namespace)
    resolved = declaration(cls).resolve(settings)
    if not isinstance(context, DataContext) or not isinstance(instrument, InstrumentSpec):
        raise TypeError("optimizer: DataContext and InstrumentSpec must be supplied")
    frozen = data.copy(deep=True)
    run_settings = resolved.snapshot()
    backtest = {
        "schemaVersion": 2,
        "settings": run_settings,
        "context": context.snapshot(),
        "instrument": asdict(instrument),
        "engineVersion": version("openbacktesting"),
    }
    execution = execution_identity(frozen, identity, backtest)
    plan_value = plan(
        cls, search, base_inputs=request, execution=execution, constraint_id=constraint_id
    )
    # Construction validation does not execute strategies; reject invalid market data before creating a database or running the first trial.
    Backtest(
        frozen, cls, context=context, instrument=instrument, **resolved.kwargs(), plotting=False
    )
    namespace = dict(namespace)
    collection = CollectionPolicy(portfolio=True, logs=False, plotting=False)

    def run_one(inputs_request):
        session = RunLogs()
        with session._capture():
            result = _run(
                namespace,
                inputs_request,
                frozen,
                context,
                instrument,
                deepcopy(run_settings),
                {"plotting": False},
                session,
                collection,
            )
        try:
            return export_result(result)
        except Exception as error:
            raise _ExportError(str(error)) from error

    return execute(
        plan_value,
        run_one,
        path,
        experiment_id=experiment_id,
        constraint=constraint,
        cancel=cancel,
        on_progress=on_progress,
    )
