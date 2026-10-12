"""Native strategy interface and indicator registration."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from difflib import get_close_matches
from itertools import chain
from typing import Literal, cast, overload

import numpy as np
import pandas as pd

from openbacktesting.broker.core import Order, OrderGroup, Position, Trade, _Broker
from openbacktesting.broker.instrument import InstrumentSpec
from openbacktesting.broker.models import (
    AccountSnapshot,
    ClosedTradeStats,
    Fill,
    OrderEvent,
    RunSummary,
)
from openbacktesting.broker.requests import OrderRequest, _Expiry, _JsonValue
from openbacktesting.broker.sizing import UNSET, _SizeIntent, select_size
from openbacktesting.data.core import _Data
from openbacktesting.data.strategy_data import DATA_NAMES, StrategyData
from openbacktesting.data.timeframe import Timeframe
from openbacktesting.helpers import _as_str, _set_legacy_module, try_
from openbacktesting.indicators.methods import TechnicalAnalysis
from openbacktesting.indicators.runtime import compute
from openbacktesting.indicators.types import IndicatorCursor, IndicatorError, IndicatorHandle
from openbacktesting.logs import StrategyLog
from openbacktesting.plotting.collector import Plotting
from openbacktesting.strategy.bar_state import BarState
from openbacktesting.strategy.inputs import ResolvedInputs


class Strategy(metaclass=ABCMeta):
    """Strategy base class: Register indicators in init and place orders from currently visible history in next.


    A trading strategy base class. Extend this class and
    override methods
    `openbacktesting.engine.Strategy.init` and
    `openbacktesting.engine.Strategy.next` to define
    your own strategy.
    """

    _input_strategy_base = True
    _reserved_data_names = DATA_NAMES | {
        "plotting",
        "timeframe",
        "bar_index",
        "bar_state",
        "log",
        "closed_trade_stats",
    }

    def __init__(self, broker, data, params):
        for cls in type(self).__mro__:
            if cls is not Strategy:
                conflicts = (
                    DATA_NAMES
                    | {
                        "ta",
                        "plotting",
                        "timeframe",
                        "bar_index",
                        "bar_state",
                        "log",
                        "closed_trade_stats",
                    }
                ).intersection(cls.__dict__)
                if conflicts:
                    name = min(conflicts)
                    raise AttributeError(f"Strategy.{name} is a reserved attribute; rename the field or method with the same name")
        self._bar_context: tuple[int, BarState] | None = None
        self._indicators = []
        self._indicator_cursor = IndicatorCursor(len(data))
        self._broker: _Broker = broker
        self._data: _Data = data
        self._strategy_data = StrategyData(data, self._indicator_cursor)
        self._ta = TechnicalAnalysis(self._register_indicator)
        self._params = self._check_params(params)

    def __setattr__(self, name, value):
        if name in DATA_NAMES | {
            "plotting",
            "timeframe",
            "bar_index",
            "bar_state",
            "log",
            "closed_trade_stats",
        }:
            raise AttributeError(f"Strategy.{name} is a reserved attribute; rename the field or parameter with the same name")
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if name in DATA_NAMES | {
            "plotting",
            "timeframe",
            "bar_index",
            "bar_state",
            "log",
            "closed_trade_stats",
        }:
            raise AttributeError(f"Strategy.{name} is a reserved attribute and cannot be deleted; rename the field with the same name")
        super().__delattr__(name)

    @staticmethod
    def _check_reserved_params(params):
        conflicts = (
            DATA_NAMES
            | {"ta", "plotting", "timeframe", "bar_index", "bar_state", "log", "closed_trade_stats"}
        ).intersection(params)
        if conflicts:
            name = min(conflicts)
            raise AttributeError(f"Strategy.{name} is a reserved attribute; rename the parameter with the same name")

    def _enter_bar(self, index: int, total: int):
        self._bar_context = (index, BarState(index == 0, index == total - 1))

    @property
    def bar_index(self) -> int:
        """Current zero-based data position; unavailable in init, on_finish, and after the run ends."""
        if self._bar_context is None:
            raise RuntimeError("bar_index: no current execution bar")
        return self._bar_context[0]

    @property
    def bar_state(self) -> BarState:
        """Frozen first/last snapshot for the current data position; early termination does not relabel the current position as the last bar."""
        if self._bar_context is None:
            raise RuntimeError("bar_state: no current execution bar")
        return self._bar_context[1]

    @property
    def timeframe(self) -> Timeframe | None:
        """This chart's timeframe; None without low-level context, with no inference from market data."""
        context = getattr(self._data, "_context", None)
        return context.timeframe if context is not None else None

    @property
    def log(self) -> StrategyLog:
        """Structured logs for the current run; use info, warning, and error inside author callbacks."""
        return self._log

    @property
    def plotting(self) -> Plotting:
        """Pure plotting-data entry point for the current run; declare in init and write during runtime callbacks."""
        return self._plotting

    @property
    def open(self) -> IndicatorHandle:
        """Open-price series for the current run; [-1] is the current value."""
        return self._strategy_data.get("open")

    @property
    def high(self) -> IndicatorHandle:
        """High-price series for the current run."""
        return self._strategy_data.get("high")

    @property
    def low(self) -> IndicatorHandle:
        """Low-price series for the current run."""
        return self._strategy_data.get("low")

    @property
    def close(self) -> IndicatorHandle:
        """Close-price series for the current run, usable directly with self.ta in init."""
        return self._strategy_data.get("close")

    @property
    def volume(self) -> IndicatorHandle:
        """Volume series; missing Volume remains NaN."""
        return self._strategy_data.get("volume")

    @property
    def hl2(self) -> IndicatorHandle:
        """(High + Low) / 2, computed lazily per run."""
        return self._strategy_data.get("hl2")

    @property
    def hlc3(self) -> IndicatorHandle:
        """(High + Low + Close) / 3。"""
        return self._strategy_data.get("hlc3")

    @property
    def hlcc4(self) -> IndicatorHandle:
        """(High + Low + Close + Close) / 4, excluding Open."""
        return self._strategy_data.get("hlcc4")

    @property
    def data_index(self) -> pd.Index:
        """Currently visible index; saved pandas objects do not update with the cursor."""
        return self.data.index

    @property
    def df(self) -> pd.DataFrame:
        """Currently visible original market-data table; no guarantee of deep copying or content isolation."""
        return self.data.df

    @property
    def pip(self) -> float:
        """Retains full-sample decimal-precision estimation; does not represent an exchange minimum step."""
        return self.data.pip

    @property
    def ta(self) -> TechnicalAnalysis:
        """Indicator entry point for the current run, such as ta.ema(length=20) or ta.macd().histogram."""
        return self._ta

    @ta.setter
    def ta(self, value):
        raise AttributeError("Strategy.ta is a reserved attribute; rename the field or parameter with the same name")

    def __repr__(self):
        return "<Strategy " + str(self) + ">"

    def __str__(self):
        params = ",".join(
            f"{i[0]}={i[1]}" for i in zip(self._params.keys(), map(_as_str, self._params.values()))
        )
        if params:
            params = "(" + params + ")"
        return f"{self.__class__.__name__}{params}"

    def _check_params(self, params):
        if isinstance(params, ResolvedInputs):
            self._resolved_inputs = params
            return params.overrides()
        self._check_reserved_params(params)
        for k, v in params.items():
            if not hasattr(self, k):
                suggestions = get_close_matches(
                    k, (attr for attr in dir(self) if not attr.startswith("_"))
                )
                hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
                raise AttributeError(
                    f"Strategy '{self.__class__.__name__}' is missing parameter '{k}'. "
                    "Strategy class should define parameters as class variables before they "
                    "can be optimized or run with." + hint
                )
            setattr(self, k, v)
        return params

    def ind(
        self,
        func: Callable,
        *args,
        name=None,
        **kwargs,
    ) -> IndicatorHandle:
        """Compute custom indicators in bulk during initialization and return read-only handles read through the backtest cursor.

        Register the same function with different parameters or reuse it across strategies. Each registration executes the
        function without sharing a custom-computation cache; prefer ``self.ta`` for built-in formulas.
        Functions receive complete history in init; authors must ensure computations depend only on current and past data.

        Args:
            func: Computation function returning one- or two-dimensional array-like output with time-axis length equal to market data.
                Series/DataFrame indices must exactly match market data; arrays align by position.
            *args: Positional arguments passed unchanged to the computation function.
            name: Display name or sequence of multi-output channel names, with length equal to the channel count.
                Defaults to the function and arguments; format fields in names are filled from computation arguments.
            **kwargs: Keyword arguments passed unchanged to the computation function.

        Returns:
            Read-only IndicatorHandle. Access named channels with ``result['middle']``;
            ``np.asarray()``, ``.s``, and ``.df`` return prefix snapshots at read time.

        Raises:
            IndicatorError: Registration outside init, changed market-data source, or misaligned pandas index.
            TypeError: name is not a string or string sequence.
            ValueError: Output shape, length, or channel-name count does not match.
            RuntimeError: User-function computation failed, with the original exception retained as cause.

        Note:
            ready defaults to all True; valid depends on finite values. next runs on every bar starting with the first;
            authors must check history length and valid for the channels they use. Invalid indicators do not suppress callbacks.
            More complex output masks are not public parameters of this entry point.
        """

        if "warmup" in kwargs:
            raise TypeError("warmup has been removed; next runs on every bar, so check indicator valid explicitly")
        if self._indicator_cursor.phase != "init":
            raise IndicatorError("invalid-phase", "custom", "Indicators may be registered only in init()")
        self._strategy_data.validate()

        def _format_name(name: str) -> str:
            return name.format(
                *map(_as_str, args), **dict(zip(kwargs.keys(), map(_as_str, kwargs.values())))
            )

        if name is None:
            params = ",".join(filter(None, map(_as_str, chain(args, kwargs.values()))))
            func_name = _as_str(func)
            name = f"{func_name}({params})" if params else f"{func_name}"
        elif isinstance(name, str):
            name = _format_name(name)
        elif try_(lambda: all(isinstance(item, str) for item in name), False):
            name = [_format_name(item) for item in name]
        else:
            raise TypeError(
                f"Unexpected `name=` type {type(name)}; expected `str` or `Sequence[str]`"
            )

        try:
            value = func(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f'Indicator "{name}" error. See traceback above.') from e

        if isinstance(value, (pd.Series, pd.DataFrame)) and not value.index.equals(self.data.index):
            raise IndicatorError("index-mismatch", name, "Indicator index must match the market-data index")
        if isinstance(value, pd.DataFrame):
            value = value.values.T

        if value is not None:
            value = try_(lambda: np.asarray(value, order="C"), None)
        is_arraylike = bool(value is not None and value.shape)

        # Optionally flip the array if the user returned e.g. `df.values`
        if is_arraylike and value.shape[0] == len(self._data):
            value = value.T

        if isinstance(name, list) and (np.atleast_2d(value).shape[0] != len(name)):
            raise ValueError(
                f"Length of `name=` ({len(name)}) must agree with the number "
                f"of arrays the indicator returns ({value.shape[0]})."
            )

        if not is_arraylike or not 1 <= value.ndim <= 2 or value.shape[-1] != len(self._data):
            raise ValueError(
                "Indicators must return (optionally a tuple of) numpy.arrays of same "
                f'length as `data` (data shape: {self._data.Close.shape}; indicator "{name}" '
                f"shape: {getattr(value, 'shape', '')}, returned value: {value})"
            )

        value = IndicatorHandle(
            value,
            name=name,
            index=self.data.index,
            cursor=self._indicator_cursor,
            metadata={"kind": "custom", "name": name, "cache": "disabled"},
        )
        self._indicators.append(value)
        return value

    def _register_indicator(
        self, indicator, *, inputs=None, backend=None, required_outputs=None, **parameters
    ):
        """Register built-in indicators internally for self.ta; the owned catalog defines output names and parameters."""
        if self._indicator_cursor.phase != "init":
            raise IndicatorError("invalid-phase", indicator, "Indicators may be registered only in init()")
        self._strategy_data.validate()
        value = compute(
            indicator,
            self.data.df,
            parameters=parameters,
            inputs=inputs,
            backend=backend,
            required_outputs=required_outputs,
            cache=self._data._indicator_cache,
            cursor=self._indicator_cursor,
        )
        self._indicators.append(value)
        return value

    @abstractmethod
    def init(self):
        """Strategy initialization entry point for precomputation and indicator registration; complete historical data is accessible.


        Initialize the strategy.
        Override this method.
        Declare indicators (with `openbacktesting.engine.Strategy.ind`).
        Precompute what needs to be precomputed or can be precomputed
        in a vectorized fashion before the strategy starts.

        If you extend composable strategies from `openbacktesting.lib`,
        make sure to call:

            super().init()
        """

    @abstractmethod
    def next(self):
        """Per-bar strategy callback, starting at input bar 0 and called once for each normally reached bar.

        Called even with insufficient or invalid indicator history; check length before [-2] and valid before consuming indicators.
        bar_index/bar_state represent the current input position and frozen first/last state.


        Main strategy runtime method, called as each new
        `openbacktesting.engine.Strategy.data`
        instance (row; full candlestick bar) becomes available.
        This is the main method where strategy decisions
        upon data precomputed in `openbacktesting.engine.Strategy.init`
        take place.

        If you extend composable strategies from `openbacktesting.lib`,
        make sure to call:

            super().next()
        """

    def on_start(self):
        """One notification after initialization completes; order submission is prohibited here."""

    def on_finish(self, summary: RunSummary):
        """Receive a frozen finish summary, including exceptional termination; trading is prohibited."""

    def on_order(self, event: OrderEvent):
        """Receive frozen order events; new requests execute no earlier than the next bar."""

    def on_fill(self, fill: Fill):
        """Receive actual fill facts; callbacks do not recursively trigger matching."""

    def _order_size(self, qty, amount, percent, reduce_only):
        self._broker._permission()
        settings = getattr(self._data, "_default_order_size", None)
        default = None
        if settings is not None:
            default = _SizeIntent(
                "qty" if settings.mode == "fixed" else "percent",
                settings.value if settings.mode == "fixed" else settings.value * 100,
                "default",
            )
        return select_size(
            qty=qty, amount=amount, percent=percent, default=default, reduce_only=reduce_only
        )

    @overload
    def buy(
        self,
        *,
        qty: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: bool = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order:
        """Explicit asset quantity; reduce-only is allowed."""

    @overload
    def buy(
        self,
        *,
        amount: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: Literal[False] = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order:
        """Explicit notional amount; reduce-only is not allowed."""

    @overload
    def buy(
        self,
        *,
        percent: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: Literal[False] = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order:
        """Explicit equity percentage; reduce-only is not allowed."""

    @overload
    def buy(
        self,
        *,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: Literal[False] = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order:
        """Omit all sizing choices to use the configured default."""

    def buy(
        self,
        *,
        qty: float = cast(float, UNSET),
        amount: float = cast(float, UNSET),
        percent: float = cast(float, UNSET),
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: bool = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order:
        """Submit an incremental order; choose one of qty/amount/percent, where percent=20 means 20% of equity.

        Omitting all choices uses the default quantity. Amount is a single-currency notional budget excluding fees;
        convert and freeze it using Close at request time, with rejection still possible at execution. Reduce-only requires explicit qty.
        """
        return self._broker.submit_order(
            self._order_size(qty, amount, percent, reduce_only),
            side="buy",
            limit=limit,
            stop=stop,
            sl=sl,
            tp=tp,
            tag=tag,
            reduce_only=reduce_only,
            expires_at=expires_at,
            valid_bars=valid_bars,
        )

    @overload
    def sell(
        self,
        *,
        qty: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: bool = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order:
        """Explicit asset quantity; reduce-only is allowed."""

    @overload
    def sell(
        self,
        *,
        amount: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: Literal[False] = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order:
        """Explicit notional amount; reduce-only is not allowed."""

    @overload
    def sell(
        self,
        *,
        percent: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: Literal[False] = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order:
        """Explicit equity percentage; reduce-only is not allowed."""

    @overload
    def sell(
        self,
        *,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: Literal[False] = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order:
        """Omit all sizing choices to use the configured default."""

    def sell(
        self,
        *,
        qty: float = cast(float, UNSET),
        amount: float = cast(float, UNSET),
        percent: float = cast(float, UNSET),
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: bool = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order:
        """Submit an incremental order; choose one of qty/amount/percent, where percent=20 means 20% of equity.

        Omitting all choices uses the default quantity. Amount is a single-currency notional budget excluding fees;
        convert and freeze it using Close at request time, with rejection still possible at execution. Reduce-only requires explicit qty.
        """
        return self._broker.submit_order(
            self._order_size(qty, amount, percent, reduce_only),
            side="sell",
            limit=limit,
            stop=stop,
            sl=sl,
            tp=tp,
            tag=tag,
            reduce_only=reduce_only,
            expires_at=expires_at,
            valid_bars=valid_bars,
        )

    @property
    def account(self) -> AccountSnapshot:
        """Frozen snapshot of current balance, equity, actual fees, and margin."""
        return self._broker.account

    @property
    def instrument(self) -> InstrumentSpec:
        """Asset rules for this run."""
        return self._broker.instrument

    def close_position(self, portion: float | None = None) -> tuple[Order, ...]:
        """Exit each lot; return an empty tuple when flat, while self.close remains market data."""
        return self.position.close(portion)

    def submit_oco(self, *, first: OrderRequest, second: OrderRequest) -> OrderGroup:
        """Atomically submit two entry requests; validate both first, prioritize first, and return a queryable group."""
        return self._broker.submit_oco(first=first, second=second)

    def order_target_quantity(
        self,
        *,
        target: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: bool = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order | None:
        """Generate a difference order from the actual net position; always validate conditions and reuse identical active targets.

        target is the target asset quantity; return None when no order is needed. Only netting mode is supported.
        All arguments must be supplied by name; limit/stop/sl/tp are absolute prices.
        Validate prices, expiration, and tags even with no difference; do not invent a buy/sell direction to check protection relationships.
        """
        return self._broker.order_target(
            target,
            {
                "limit": limit,
                "stop": stop,
                "sl": sl,
                "tp": tp,
                "tag": tag,
                "reduce_only": reduce_only,
                "expires_at": expires_at,
                "valid_bars": valid_bars,
            },
        )

    def order_target_value(
        self,
        *,
        target: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: bool = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order | None:
        """Convert target net notional to quantity using Close at request time; explicit conditions match quantity targets."""
        from openbacktesting.broker.models import finite

        return self.order_target_quantity(
            target=finite(target, "target") / self.close[-1],
            limit=limit,
            stop=stop,
            sl=sl,
            tp=tp,
            tag=tag,
            reduce_only=reduce_only,
            expires_at=expires_at,
            valid_bars=valid_bars,
        )

    def order_target_percent(
        self,
        *,
        target: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        reduce_only: bool = False,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> Order | None:
        """Determine target net notional from equity percentage at request time; no continuous rebalancing or guaranteed fill weight."""
        from openbacktesting.broker.models import finite

        if self.equity <= 0:
            raise ValueError("Target percentage requires positive equity")
        return self.order_target_value(
            target=finite(target, "target") * self.equity,
            limit=limit,
            stop=stop,
            sl=sl,
            tp=tp,
            tag=tag,
            reduce_only=reduce_only,
            expires_at=expires_at,
            valid_bars=valid_bars,
        )

    @property
    def equity(self) -> float:
        """Current account equity, including cash and position value.

        Current account equity (cash plus assets)."""
        return self._broker.equity

    @property
    def data(self) -> _Data:
        """Currently visible original market-data entry point; full history in init and only the current prefix in next.


        Price data, roughly as passed into
        `openbacktesting.engine.Backtest.__init__`,
        but with two significant exceptions:

        * `data` is _not_ a DataFrame, but a custom structure
          that serves customized numpy arrays for reasons of performance
          and convenience. Besides OHLCV columns, `.index` and length,
          it offers `.pip` property, the smallest price unit of change.
        * Within `openbacktesting.engine.Strategy.init`, `data` arrays
          are available in full length, as passed into
          `openbacktesting.engine.Backtest.__init__`
          (for precomputing indicators and such). However, within
          `openbacktesting.engine.Strategy.next`, `data` arrays are
          only as long as the current iteration, simulating gradual
          price point revelation. In each call of
          `openbacktesting.engine.Strategy.next` (iteratively called by
          `openbacktesting.engine.Backtest` internally),
          the last array value (e.g. `data.Close[-1]`)
          is always the **most recent** value.
        * If you need data arrays (e.g. `data.Close`) to be indexed
          **Pandas series**, you can call their `.s` accessor
          (e.g. `data.Close.s`). If you need the whole of data
          as a **DataFrame**, use `.df` accessor (i.e. `data.df`).
        """
        return self._data

    @property
    def position(self) -> Position:
        """Current net-position aggregate, supporting size/profit reads and closure requests.

        Instance of `openbacktesting.engine.Position`."""
        return self._broker.position

    @property
    def orders(self) -> tuple[Order, ...]:
        """Orders awaiting execution; cancel may be called on these orders.

        List of orders (see `Order`) waiting for execution."""
        return tuple(self._broker.orders)

    @property
    def trades(self) -> tuple[Trade, ...]:
        """Currently held trades, distinct from settled closed_trades.

        List of active trades (see `Trade`)."""
        return tuple(self._broker.trades)

    @property
    def closed_trade_stats(self) -> ClosedTradeStats:
        """Read frozen statistics for closed portions, including allocated fees and excluding unrealized profit or loss.

        Reads do not scan history; available throughout the lifecycle and after the run ends.
        same_close results are not visible before execution; saved values do not change with later fills.
        """
        return self._broker._closed_stats

    @property
    def closed_trades(self) -> tuple[Trade, ...]:
        """Completed trades for individual-trade analysis.

        List of settled trades (see `Trade`)."""
        return tuple(self._broker.closed_trades)


_set_legacy_module(Strategy, "openbacktesting.engine")
