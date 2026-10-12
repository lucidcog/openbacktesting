"""Native backtest configuration, lifecycle, and per-bar execution coordination."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from contextlib import contextmanager
from copy import copy
from functools import partial
from importlib.metadata import version
from numbers import Number

import numpy as np
import pandas as pd

from openbacktesting.broker.commission import Commission, normalize_commission
from openbacktesting.broker.core import _Broker
from openbacktesting.broker.instrument import InstrumentSpec
from openbacktesting.broker.models import Fill, RunSummary
from openbacktesting.broker.observations import Observations
from openbacktesting.data.context import DataContext
from openbacktesting.data.core import _Data
from openbacktesting.helpers import _set_legacy_module
from openbacktesting.indicators.runtime import (
    DEFAULT_CACHE_BYTES,
    IndicatorCache,
    optimization_cache,
)
from openbacktesting.logs import StrategyLog, _Collector
from openbacktesting.plotting.collector import Plotting
from openbacktesting.plotting.types import PlottingError, PlottingLimits
from openbacktesting.portfolio.rates import validate_risk_free_rate
from openbacktesting.portfolio.snapshot import capture_snapshot
from openbacktesting.portfolio.stats import compute_stats
from openbacktesting.portfolio.trading import trading_results
from openbacktesting.simulation.collection import DEFAULT_COLLECTION, CollectionPolicy
from openbacktesting.simulation.config import DefaultOrderSize, validate_order_size
from openbacktesting.simulation.optimization import _optimize
from openbacktesting.simulation.parallel import SharedMemoryManager
from openbacktesting.strategy.base import Strategy
from openbacktesting.strategy.inputs import _definitions, resolve_native, resolve_request
from openbacktesting.util import _tqdm


class Backtest:
    """Store single-asset historical market data, strategy, and linear margin-account configuration.

    data OHLC must contain finite positive prices, with an ordered unique index. instrument specifies quantity steps and an optional price grid.
    cash is the initial balance; margin is the notional margin fraction; hedging controls retention of two-sided lots.
    commission may be a rate, (fixed fee, rate), Commission, or pure fee function, charged once per actual execution.
    spread and slippage apply to every buy/sell execution; slippage never permits orders to cross their limits.
    execution_timing supports next_open or same_close; end_policy supports mark_to_market or close_at_last_close.
    allow_short controls new short positions; max_gross_exposure caps gross notional/equity; valid reductions are always allowed.
    exclusive_orders cancels previous entries and submits exits for existing lots when a new ordinary order is submitted.
    context is optional; when provided, it requires a timezone-aware index and converts display timezone on a copy; strategies can read self.timeframe.
    risk_free_rate is an annualized fraction affecting statistics only; default_order_size supplies the request budget when qty is omitted.
    Low-level construction does not automatically merge @backtest settings; runtime handles declaration adoption.
    No legacy size-fraction inference, price scaling, cross-currency trading, volume-based partial fills, or live execution.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        strategy: type[Strategy],
        *,
        cash: float = 10_000,
        spread: float = 0.0,
        commission: float
        | tuple[float, float]
        | Commission
        | Callable[[float, float], float] = 0.0,
        risk_free_rate: float = 0.0,
        default_order_size: DefaultOrderSize | None = None,
        margin: float = 1.0,
        execution_timing="next_open",
        instrument=None,
        slippage=None,
        allow_short=True,
        max_gross_exposure=None,
        hedging=False,
        exclusive_orders=False,
        end_policy="mark_to_market",
        indicator_cache_bytes=DEFAULT_CACHE_BYTES,
        context: DataContext | None = None,
        plotting: bool = True,
        plotting_limits: PlottingLimits | None = None,
        _collection: CollectionPolicy = DEFAULT_COLLECTION,
    ):
        if type(plotting) is not bool:
            raise PlottingError("invalid-option", "plotting must be bool")
        if plotting_limits is not None and not isinstance(plotting_limits, PlottingLimits):
            raise PlottingError("invalid-limit", "plotting_limits must be PlottingLimits")
        self._plotting_enabled = plotting and _collection.plotting
        self._portfolio_enabled = _collection.portfolio
        self._plotting_limits = plotting_limits
        self._indicator_cache_bytes = IndicatorCache(indicator_cache_bytes).budget
        if not (isinstance(strategy, type) and issubclass(strategy, Strategy)):
            raise TypeError("`strategy` must be a Strategy sub-type")
        if not isinstance(data, pd.DataFrame):
            raise TypeError("`data` must be a pandas.DataFrame with columns")
        if not isinstance(spread, Number):
            raise TypeError("`spread` must be a float value, percent of entry order price")
        self._risk_free_rate = validate_risk_free_rate(risk_free_rate)
        self._default_order_size = validate_order_size(default_order_size)
        if not callable(commission):
            normalize_commission(commission)

        data = data.copy(deep=False)
        if context is not None:
            if not isinstance(context, DataContext):
                raise TypeError("context must be DataContext or None")
            if not isinstance(data.index, pd.DatetimeIndex) or data.index.tz is None:
                raise ValueError("Market data must use a timezone-aware DatetimeIndex when context is provided")
            data.index = data.index.tz_convert(context.timezone)
        self._context = context

        # Convert index to datetime index
        if (
            not isinstance(data.index, pd.DatetimeIndex)
            and not isinstance(data.index, pd.RangeIndex)
            and
            # Numeric index with most large numbers
            (
                data.index.is_numeric()
                and (data.index > pd.Timestamp("1975").timestamp()).mean() > 0.8
            )
        ):
            try:
                data.index = pd.to_datetime(data.index, infer_datetime_format=True)
            except ValueError:
                pass

        if "Volume" not in data:
            data["Volume"] = np.nan

        if len(data) == 0:
            raise ValueError("OHLC `data` is empty")
        if len(data.columns.intersection({"Open", "High", "Low", "Close", "Volume"})) != 5:
            raise ValueError(
                "`data` must be a pandas.DataFrame with columns "
                "'Open', 'High', 'Low', 'Close', and (optionally) 'Volume'"
            )
        if data[["Open", "High", "Low", "Close"]].isnull().values.any():
            raise ValueError(
                "Some OHLC values are missing (NaN). "
                "Please strip those lines with `df.dropna()` or "
                "fill them in with `df.interpolate()` or whatever."
            )
        instrument = instrument or InstrumentSpec()
        instrument.validate_data(data)
        if execution_timing not in ("next_open", "same_close"):
            raise ValueError("execution_timing must be next_open or same_close")
        if end_policy not in ("mark_to_market", "close_at_last_close"):
            raise ValueError("end_policy must be mark_to_market or close_at_last_close")
        if not isinstance(data.index, pd.DatetimeIndex):
            warnings.warn(
                "Data index is not datetime. Assuming simple periods, "
                "but `pd.DateTimeIndex` is advised.",
                stacklevel=2,
            )

        self._data: pd.DataFrame = data
        self._broker = partial(
            _Broker,
            cash=cash,
            spread=spread,
            commission=commission,
            margin=margin,
            execution_timing=execution_timing,
            instrument=instrument,
            slippage=slippage,
            allow_short=allow_short,
            max_gross_exposure=max_gross_exposure,
            hedging=hedging,
            exclusive_orders=exclusive_orders,
            index=data.index,
        )
        self._strategy = strategy
        self._results: pd.Series | None = None
        self._end_policy = end_policy
        self._log_collector = None
        self._logs_enabled = _collection.logs
        self._log_running = False
        self._log_delegate = None

    def run_inputs(self, request) -> pd.Series:
        """Submit an input request with schemaVersion/schemaHash/values keyed by unique title."""
        with self._log_scope() as logs:
            resolved = resolve_request(self._strategy, request)
            self._log_delegate = logs
            return self.run(**resolved.overrides())

    def get_logs(self) -> list[dict[str, str | int | None]]:
        """Return an independent copy of all strategy logs for this run; empty before any run.

        Failures preserve written records; new run/run_inputs/optimize calls clear old logs.
        Logs contain time, bar_index, source file, and line; retained in full by default without silent truncation.
        """
        logs = getattr(self, "_log_collector", None)
        return [] if logs is None else logs.snapshot()

    @contextmanager
    def _log_scope(self):
        if getattr(self, "_log_running", False):
            raise RuntimeError("Backtest cannot run reentrantly")
        self._log_collector = logs = _Collector(enabled=getattr(self, "_logs_enabled", True))
        self._log_running = True
        try:
            yield logs
        finally:
            logs.close()
            self._log_running = False
            self._log_delegate = None

    def run(self, **kwargs) -> pd.Series:
        """Backtest strategy parameters and return a statistics Series, plain-value ledger tables, and an optional diagnostic strategy.

        Public statistics keys:
        Start, End, Duration, Exposure Time [%]
        Equity Final [$], Equity Peak [$], Return [%], Buy & Hold Return [%]
        Return (Ann.) [%], Volatility (Ann.) [%], CAGR [%], Sharpe Ratio
        Sortino Ratio, Calmar Ratio, Alpha [%], Beta
        Max. Drawdown [%], Avg. Drawdown [%], Max. Drawdown Duration, Avg. Drawdown Duration
        # Trades, Win Rate [%], Best Trade [%], Worst Trade [%]
        Avg. Trade [%], Max. Trade Duration, Avg. Trade Duration, Profit Factor
        Expectancy [%], SQN, Kelly Criterion, Commissions [$]
        # Closed Lots, _strategy, _equity_curve, _trades
        _orders, _order_sizing, _order_events, _fills, _trade_allocations
        _positions, _account_curve, _final_account, _open_trades

        Order and fill events are not gated by indicator NaN; next runs on every bar starting with the first.
        Retain account and gross exposure on each normal bar; record terminal handling in a separate terminal snapshot.
        Result attrs contain trading-policy version, configuration, and input snapshots; _strategy is not required to reconstruct trading facts.
        """
        delegated = getattr(self, "_log_delegate", None)
        if delegated is not None:
            self._log_delegate = None
            return self._run(kwargs, delegated)
        with self._log_scope() as logs:
            return self._run(kwargs, logs)

    def _run(self, kwargs, logs):
        if not hasattr(self, "_end_policy"):
            raise TypeError(
                "Backtest state from 0.1 cannot resume execution; reconstruct Backtest using execution_timing/end_policy"
            )
        resolved = resolve_native(self._strategy, kwargs)
        data = _Data(self._data.copy(deep=True))
        data._context = self._context
        data._default_order_size = self._default_order_size
        data._indicator_cache = getattr(self, "_indicator_cache", None) or IndicatorCache(
            getattr(self, "_indicator_cache_bytes", DEFAULT_CACHE_BYTES)
        )
        broker: _Broker = self._broker(data=data)
        if getattr(self, "_portfolio_enabled", True):
            broker.observations = Observations()
        strategy: Strategy = self._strategy(
            broker, data, resolved if resolved is not None else kwargs
        )

        strategy._log = StrategyLog(logs)

        def invoke(phase, callback, *args):
            bar_index = None if strategy._bar_context is None else strategy._bar_context[0]
            bar_time, time_kind = None, "none"
            if bar_index is not None:
                if isinstance(self._data.index, pd.DatetimeIndex):
                    label = self._data.index[bar_index]
                    bar_time = label.isoformat()
                    time_kind = "aware-datetime" if label.tzinfo is not None else "naive-datetime"
                else:
                    time_kind = "ordinal"
            with logs.phase(phase, bar_index, bar_time, time_kind):
                return callback(*args)

        collector = Plotting(
            self._data.index,
            strategy._indicator_cursor,
            enabled=self._plotting_enabled,
            limits=self._plotting_limits,
        )
        strategy._plotting = collector
        finished = False

        def notify(*, terminal=False):
            # Closed notification batches: notifications produced by callbacks wait for the next notification point and cannot be drained recursively.
            batch, broker._notifications = broker._notifications, []
            broker.phase = "terminal" if terminal else "notify"
            for event in batch:
                phase = "on_fill" if isinstance(event, Fill) else "on_order"
                collector._enter(phase.replace("on_", "terminal_") if terminal else phase)
                invoke(
                    phase.replace("on_", "terminal_") if terminal else phase,
                    strategy.on_fill if isinstance(event, Fill) else strategy.on_order,
                    event,
                )
            collector._enter("idle")

        try:
            collector._enter("init")
            invoke("init", strategy.init)
            collector._enter("idle")
            strategy._strategy_data.validate()
            data._update()
            broker.instrument.validate_data(data.df)
            strategy._indicator_cursor.phase = "run"
            data._set_length(1)
            strategy._indicator_cursor.length = 1
            broker.phase = "start"
            collector._enter("start")
            strategy._enter_bar(0, len(self._data))
            invoke("on_start", strategy.on_start)
            collector._enter("idle")
            reason = "end_of_data"
            with np.errstate(invalid="ignore"):
                for i in _tqdm(
                    range(len(self._data)),
                    desc=self.run.__qualname__,
                    unit="bar",
                    mininterval=2,
                    miniters=100,
                ):
                    data._set_length(i + 1)
                    strategy._indicator_cursor.length = i + 1
                    strategy._enter_bar(i, len(self._data))
                    broker._i = i
                    collector._enter("idle", i)
                    broker.process()
                    if broker.equity <= 0:
                        broker.capture()
                        reason = "insolvent"
                        broker.finish(liquidate=True, reason=reason)
                        broker._equity[i:] = broker.equity
                        notify(terminal=True)
                        break
                    notify()
                    broker.phase = "next"
                    collector._enter("next", i)
                    invoke("next", strategy.next)
                    collector._enter("idle")
                    if broker.execution_timing == "same_close":
                        broker.process(close=True)
                    notify()
                    broker.update_trails()
                    broker.capture()
                else:
                    broker.finish(liquidate=self._end_policy == "close_at_last_close")
                    notify(terminal=True)
                strategy._bar_context = None
                broker.phase = "finish"
                finished = True
                collector._enter("finish")
                invoke("on_finish", strategy.on_finish, RunSummary(reason, broker.account))
                data._set_length(len(self._data))
                strategy._indicator_cursor.length = len(self._data)
                strategy._indicator_cursor.phase = "complete"
                self._results = compute_stats(
                    trades=broker.closed_trades,
                    equity=broker._equity,
                    ohlc_data=self._data,
                    risk_free_rate=self._risk_free_rate,
                    strategy_instance=strategy,
                    exposure=broker._exposure,
                    initial_equity=broker.ledger.initial_balance,
                )
                self._results = trading_results(self._results, broker, self._end_policy)
                self._results.attrs["statistics_risk_free_rate"] = self._risk_free_rate
                self._results.attrs["statistics_initial_equity"] = broker.ledger.initial_balance
            if resolved is not None:
                self._results.attrs["input_snapshot"] = resolved.snapshot() | {
                    "engineVersion": version("openbacktesting")
                }
            self._results.attrs["indicator_snapshot"] = {
                "engineVersion": version("openbacktesting"),
                "indicators": [indicator.metadata for indicator in strategy._indicators],
            }
            snapshot = collector._finish(self._results, self._data, reason)
            if snapshot is not None:
                self._results.attrs["plotting_result"] = snapshot
            self._results.attrs["strategy_logs"] = logs.snapshot()
            if broker.observations is not None:
                self._results.attrs["portfolio_snapshot"] = capture_snapshot(
                    self._results,
                    self._data,
                    broker.observations,
                    reason,
                    self._context.snapshot() if self._context else None,
                )
            return self._results
        except BaseException as error:
            if not finished:
                strategy._bar_context = None
                broker.phase = "finish"
                finished = True
                try:
                    collector._enter("finish")
                    invoke(
                        "on_finish",
                        strategy.on_finish,
                        RunSummary("error", broker.account, repr(error)),
                    )
                except BaseException as finish_error:  # noqa: BLE001 — preserve the primary exception and attach finish-hook failures
                    error.add_note(f"on_finish also failed: {finish_error!r}")
            raise
        finally:
            strategy._bar_context = None
            collector._close()
            data._set_length(len(self._data))
            strategy._indicator_cursor.length = len(self._data)
            strategy._indicator_cursor.phase = "complete"
            data._indicator_cache = None
            broker.phase = "finished"

    def optimize(
        self,
        *,
        maximize: str | Callable[[pd.Series], float] = "SQN",
        method: str = "grid",
        max_tries: float | None = None,
        constraint: Callable[[dict], bool] | None = None,
        return_heatmap: bool = False,
        return_optimization: bool = False,
        random_state: int | None = None,
        **kwargs,
    ) -> pd.Series | tuple[pd.Series, pd.Series] | tuple[pd.Series, pd.Series, dict]:
        """Search strategy-parameter combinations and select results by a specified statistic or scoring function.


        Optimize strategy parameters to an optimal combination.
        Returns result `pd.Series` of the best run.

        `maximize` is a string key from the
        `openbacktesting.engine.Backtest.run`-returned results series,
        or a function that accepts this series object and returns a number;
        the higher the better. By default, the method maximizes
        Van Tharp's [System Quality Number](https://altpower.app/?q=System+Quality+Number).

        `method` is the optimization method. Currently two methods are supported:

        * `"grid"` which does an exhaustive (or randomized) search over the
          cartesian product of parameter combinations, and
        * `"sambo"` which finds close-to-optimal strategy parameters using
          [model-based optimization], making at most `max_tries` evaluations.

        [model-based optimization]: https://sambo-optimization.github.io

        `max_tries` is the maximal number of strategy runs to perform.
        If `method="grid"`, this results in randomized grid search.
        If `max_tries` is a floating value between (0, 1], this sets the
        number of runs to approximately that fraction of full grid space.
        Alternatively, if integer, it denotes the absolute maximum number
        of evaluations. If unspecified (default), grid search is exhaustive,
        whereas for `method="sambo"`, `max_tries` is set to 200.

        `constraint` is a function that accepts a dict-like object of
        parameters (with values) and returns `True` when the combination
        is admissible to test with. By default, any parameters combination
        is considered admissible.

        If `return_heatmap` is `True`, besides returning the result
        series, an additional `pd.Series` is returned with a multiindex
        of all admissible parameter combinations, which can be further
        inspected as a table of parameter combinations and objective values.

        If `return_optimization` is True and `method = 'sambo'`,
        in addition to result series (and maybe heatmap), return raw
        [`scipy.optimize.OptimizeResult`][OptimizeResult] for further
        inspection by the caller.

        [OptimizeResult]: https://sambo-optimization.github.io/doc/sambo/#sambo.OptimizeResult
        [SAMBO]: https://sambo-optimization.github.io

        If you want reproducible optimization results, set `random_state`
        to a fixed integer random seed.

        Additional keyword arguments represent strategy arguments with
        list-like collections of possible values. For example, the following
        code finds and returns the "best" of the 7 admissible (of the
        9 possible) parameter combinations:

            best_stats = backtest.optimize(sma1=[5, 10, 15], sma2=[10, 20, 40],
                                           constraint=lambda p: p.sma1 < p.sma2)
        """
        if getattr(self, "_log_running", False):
            raise RuntimeError("Backtest cannot optimize reentrantly")
        self._log_collector = None
        return _optimize(
            self,
            Backtest._mp_task,
            maximize=maximize,
            method=method,
            max_tries=max_tries,
            constraint=constraint,
            return_heatmap=return_heatmap,
            return_optimization=return_optimization,
            random_state=random_state,
            **kwargs,
        )

    @staticmethod
    def _mp_task(arg):
        bt, data_shm, params_batch = arg
        # Thread pools receive the same template object; batches must isolate mutable run state such as _data/_results.
        bt = copy(bt)
        bt._plotting_enabled = False
        bt._logs_enabled = False
        bt._log_collector = None
        bt._data, shm = SharedMemoryManager.shm2df(data_shm)
        try:
            token = getattr(bt, "_indicator_cache_token", None)
            if token is not None:
                bt._indicator_cache = optimization_cache(
                    token, getattr(bt, "_indicator_cache_bytes", DEFAULT_CACHE_BYTES)
                )
            declared = bool(_definitions(bt._strategy))
            return [
                stats.filter(regex="^[^_]") if stats["# Trades"] else None
                for stats in (
                    bt.run_inputs(params) if declared else bt.run(**params)
                    for params in params_batch
                )
            ]
        finally:
            for shmem in shm:
                shmem.close()


_set_legacy_module(Backtest, "openbacktesting.engine")
