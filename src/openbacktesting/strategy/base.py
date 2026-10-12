"""原生策略接口与指标登记。"""

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
    """策略基类：在 init 登记指标，在 next 根据当前可见历史下单。


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
                    raise AttributeError(f"Strategy.{name} 是保留属性，请将同名字段或方法改名")
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
            raise AttributeError(f"Strategy.{name} 是保留属性，请将同名字段或参数改名")
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
            raise AttributeError(f"Strategy.{name} 是保留属性，不可删除；请将同名字段改名")
        super().__delattr__(name)

    @staticmethod
    def _check_reserved_params(params):
        conflicts = (
            DATA_NAMES
            | {"ta", "plotting", "timeframe", "bar_index", "bar_state", "log", "closed_trade_stats"}
        ).intersection(params)
        if conflicts:
            name = min(conflicts)
            raise AttributeError(f"Strategy.{name} 是保留属性，请将同名参数改名")

    def _enter_bar(self, index: int, total: int):
        self._bar_context = (index, BarState(index == 0, index == total - 1))

    @property
    def bar_index(self) -> int:
        """当前零起点数据位置；init、on_finish 和运行结束后不可读。"""
        if self._bar_context is None:
            raise RuntimeError("bar_index: 不存在当前执行 bar")
        return self._bar_context[0]

    @property
    def bar_state(self) -> BarState:
        """当前数据首尾的冻结快照；提前终止不会将当前位置改称末根。"""
        if self._bar_context is None:
            raise RuntimeError("bar_state: 不存在当前执行 bar")
        return self._bar_context[1]

    @property
    def timeframe(self) -> Timeframe | None:
        """本次图表周期；低层未提供上下文时为 None，不从行情猜测。"""
        context = getattr(self._data, "_context", None)
        return context.timeframe if context is not None else None

    @property
    def log(self) -> StrategyLog:
        """当前运行的结构化日志；在作者回调中使用 info、warning 和 error。"""
        return self._log

    @property
    def plotting(self) -> Plotting:
        """当前运行的纯数据绘图入口；init 声明，运行回调写入。"""
        return self._plotting

    @property
    def open(self) -> IndicatorHandle:
        """当前运行的开盘价序列；[-1] 为当前值。"""
        return self._strategy_data.get("open")

    @property
    def high(self) -> IndicatorHandle:
        """当前运行的最高价序列。"""
        return self._strategy_data.get("high")

    @property
    def low(self) -> IndicatorHandle:
        """当前运行的最低价序列。"""
        return self._strategy_data.get("low")

    @property
    def close(self) -> IndicatorHandle:
        """当前运行的收盘价序列，可在 init 直接传给 self.ta。"""
        return self._strategy_data.get("close")

    @property
    def volume(self) -> IndicatorHandle:
        """成交量序列；缺失 Volume 保留 NaN。"""
        return self._strategy_data.get("volume")

    @property
    def hl2(self) -> IndicatorHandle:
        """(High + Low) / 2，按运行惰性计算。"""
        return self._strategy_data.get("hl2")

    @property
    def hlc3(self) -> IndicatorHandle:
        """(High + Low + Close) / 3。"""
        return self._strategy_data.get("hlc3")

    @property
    def hlcc4(self) -> IndicatorHandle:
        """(High + Low + Close + Close) / 4，不包含 Open。"""
        return self._strategy_data.get("hlcc4")

    @property
    def data_index(self) -> pd.Index:
        """当前可见索引；保存的 pandas 对象不随游标更新。"""
        return self.data.index

    @property
    def df(self) -> pd.DataFrame:
        """当前可见的原行情表；不承诺深拷贝或内容隔离。"""
        return self.data.df

    @property
    def pip(self) -> float:
        """沿用全样本小数位精度估计，不代表交易所最小步长。"""
        return self.data.pip

    @property
    def ta(self) -> TechnicalAnalysis:
        """当前运行的指标入口，例如 ta.ema(length=20)、ta.macd().histogram。"""
        return self._ta

    @ta.setter
    def ta(self, value):
        raise AttributeError("Strategy.ta 是保留属性，请将同名字段或参数改名")

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
        """在初始化阶段批量计算自定义指标，返回随回测游标读取的只读句柄。

        同一函数可按不同参数登记多次，也可供多个策略复用。每次登记均执行
        函数，不共享自定义计算缓存；内置公式优先使用 ``self.ta``。
        函数在 init 中接收完整历史，作者须保证计算只依赖当前及过去数据。

        Args:
            func: 返回一维或二维 array-like 的计算函数，时间轴长度须等于行情。
                Series/DataFrame 的索引须与行情完全一致；数组按位置对齐。
            *args: 原样传给计算函数的位置参数。
            name: 展示名称或多输出的通道名称序列，序列长度须与通道数一致。
                默认由函数和参数组成，名称中的格式字段由计算参数填充。
            **kwargs: 原样传给计算函数的关键字参数。

        Returns:
            只读 IndicatorHandle。具名通道可用 ``result['middle']`` 读取；
            ``np.asarray()``、``.s`` 和 ``.df`` 得到读取时的前缀快照。

        Raises:
            IndicatorError: 非 init 阶段登记、行情来源已改变或 pandas 索引错位。
            TypeError: name 不是字符串或字符串序列。
            ValueError: 输出形状、长度或通道名称数量不匹配。
            RuntimeError: 用户函数计算失败，原异常保留为 cause。

        Note:
            默认 ready 全真，valid 由有限值决定；next 从首根逐根执行，
            作者须自行检查历史长度和所用通道的 valid。指标无效不抑制回调。
            更复杂的输出掩码不是此入口的公开参数。
        """

        if "warmup" in kwargs:
            raise TypeError("warmup 已移除；next 逐根执行，请显式检查指标 valid")
        if self._indicator_cursor.phase != "init":
            raise IndicatorError("invalid-phase", "custom", "指标只允许在 init() 登记")
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
            raise IndicatorError("index-mismatch", name, "指标索引必须与行情 index 一致")
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
        """供 self.ta 内部登记内置指标；输出名和参数由自有目录定义。"""
        if self._indicator_cursor.phase != "init":
            raise IndicatorError("invalid-phase", indicator, "指标只允许在 init() 登记")
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
        """策略初始化入口，用于预计算及登记指标；可以访问完整历史数据。


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
        """逐根策略回调，从输入第 0 根开始，每根正常到达的 bar 调用一次。

        指标历史不足或无效也会调用；读取 [-2] 前检查长度，消费指标前检查 valid。
        bar_index/bar_state 表示当前输入位置及冻结首尾状态。


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
        """初始化完成后的单次通知；此时不可下单。"""

    def on_finish(self, summary: RunSummary):
        """接收冻结结束摘要；异常结束也调用，禁止交易。"""

    def on_order(self, event: OrderEvent):
        """接收冻结订单事件；新请求最早于下一根执行。"""

    def on_fill(self, fill: Fill):
        """接收实际成交事实；回调不递归触发撮合。"""

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
        """显式资产数量；允许只减仓。"""

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
        """显式名义金额；不允许只减仓。"""

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
        """显式权益百分数；不允许只减仓。"""

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
        """省略全部规模，使用已配置默认值。"""

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
        """提交增量订单；qty/amount/percent 三选一，percent=20 表示权益20%。

        全部省略时使用默认数量。金额为单币种名义预算，不含费用；
        按请求时 Close 换算并冻结，成交时仍可能拒绝。只减仓须显式 qty。
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
        """显式资产数量；允许只减仓。"""

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
        """显式名义金额；不允许只减仓。"""

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
        """显式权益百分数；不允许只减仓。"""

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
        """省略全部规模，使用已配置默认值。"""

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
        """提交增量订单；qty/amount/percent 三选一，percent=20 表示权益20%。

        全部省略时使用默认数量。金额为单币种名义预算，不含费用；
        按请求时 Close 换算并冻结，成交时仍可能拒绝。只减仓须显式 qty。
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
        """当前余额、权益、实际费用及保证金的冻结快照。"""
        return self._broker.account

    @property
    def instrument(self) -> InstrumentSpec:
        """本次运行的资产规则。"""
        return self._broker.instrument

    def close_position(self, portion: float | None = None) -> tuple[Order, ...]:
        """逐批次退出；空仓返回空元组，self.close仍是行情。"""
        return self.position.close(portion)

    def submit_oco(self, *, first: OrderRequest, second: OrderRequest) -> OrderGroup:
        """原子提交两个入场请求；先验证两笔，first优先，返回可查询组。"""
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
        """按实际净仓生成差额订单；条件始终校验，相同活动目标复用。

        target 为目标资产数量；无需下单时返回 None。仅支持净额模式。
        所有参数必须按名称提供，limit/stop/sl/tp 均为绝对价格。
        无差额时仍校验价格、期限和标签，但不虚构买卖方向检查保护关系。
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
        """以请求时Close把目标净名义换算为数量；显式条件与数量目标一致。"""
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
        """以请求时权益比例确定目标净名义；不持续再平衡或保证成交权重。"""
        from openbacktesting.broker.models import finite

        if self.equity <= 0:
            raise ValueError("目标比例要求正权益")
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
        """当前账户权益，包含现金和持仓价值。

        Current account equity (cash plus assets)."""
        return self._broker.equity

    @property
    def data(self) -> _Data:
        """当前可见的原始行情访问入口；在 init 中可见全历史，next 中只可见当前前缀。


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
        """当前净仓位汇总，可读取规模、盈亏或请求平仓。

        Instance of `openbacktesting.engine.Position`."""
        return self._broker.position

    @property
    def orders(self) -> tuple[Order, ...]:
        """等待执行的订单列表，可对其中订单调用 cancel。

        List of orders (see `Order`) waiting for execution."""
        return tuple(self._broker.orders)

    @property
    def trades(self) -> tuple[Trade, ...]:
        """当前仍持有的交易列表，区别于已结算的 closed_trades。

        List of active trades (see `Trade`)."""
        return tuple(self._broker.trades)

    @property
    def closed_trade_stats(self) -> ClosedTradeStats:
        """读取冻结的已关闭片段统计，包含已分摊费用，不包含浮盈亏。

        每次读取不扫描历史；所有生命周期及运行结束后均可读。
        same_close 成交前不可提前看到其结果；保存的值不随新成交变化。
        """
        return self._broker._closed_stats

    @property
    def closed_trades(self) -> tuple[Trade, ...]:
        """已完成的交易列表，供逐笔分析使用。

        List of settled trades (see `Trade`)."""
        return tuple(self._broker.closed_trades)


_set_legacy_module(Strategy, "openbacktesting.engine")
