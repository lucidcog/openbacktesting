"""作者订单描述与无交易副作用的公共参数校验。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, cast, overload

import pandas as pd

from openbacktesting.broker.models import finite, freeze_tag
from openbacktesting.broker.sizing import UNSET, _SizeIntent, select_size

type _JsonValue = str | int | float | bool | None | list["_JsonValue"] | dict[str, "_JsonValue"]
type _Expiry = datetime | pd.Timestamp | str


def _normalize_conditions(
    *,
    limit=None,
    stop=None,
    sl=None,
    tp=None,
    tag=None,
    reduce_only=False,
    expires_at=None,
    valid_bars=None,
) -> dict:
    """规范化无须账户或品种的条件；不修改调用方数据。"""
    if type(reduce_only) is not bool:
        raise TypeError("reduce_only必须为bool")
    prices = {
        name: None if value is None else finite(value, name, positive=True)
        for name, value in (("limit", limit), ("stop", stop), ("sl", sl), ("tp", tp))
    }
    if expires_at is not None and valid_bars is not None:
        raise ValueError("expires_at与valid_bars互斥")
    if valid_bars is not None and (
        isinstance(valid_bars, bool) or not isinstance(valid_bars, int) or valid_bars <= 0
    ):
        raise ValueError("valid_bars必须为正整数")
    if expires_at is not None:
        if not isinstance(expires_at, (datetime, pd.Timestamp, str)):
            raise TypeError("expires_at必须为带时区的时间或字符串")
        expires_at = pd.Timestamp(expires_at)
        if pd.isna(expires_at):
            raise ValueError("expires_at不可为NaT")
        if expires_at.tzinfo is None:
            raise ValueError("绝对到期必须带时区")
    return prices | {
        "reduce_only": reduce_only,
        "expires_at": expires_at,
        "valid_bars": valid_bars,
        "tag_json": freeze_tag(tag),
    }


@dataclass(frozen=True, init=False)
class OrderRequest:
    """待提交的冻结入场请求；构造不会登记订单，可在初始化阶段准备。

    所有参数必须按名称提供。品种精度、行情时区和保护方向在提交时校验。
    ``tag`` 支持 JSON 纯值；构造时固化，读取返回独立副本。

    Args:
        side: 买入 buy 或卖出 sell。
        qty: 有限正资产数量，与 amount/percent 三选一，不使用默认预算。
        amount: 有限正名义金额，在提交时按 Close 换算，不预留费用。
        percent: (0,100] 的权益百分数，20 表示 20%，在提交时计算。
        limit: 入场限价，None 表示没有限价条件。
        stop: 入场触发价，与入场后的 sl 不同。
        sl: 入场后的绝对止损价。
        tp: 入场后的绝对止盈价。
        tag: 可选用户标签，不参与撮合条件。
        expires_at: 带时区的绝对到期时间，与 valid_bars 互斥。
        valid_bars: 提交后允许执行的 bar 数，必须为正整数。

    Raises:
        TypeError: 参数类型、命名或标签类型不合法。
        ValueError: 数量、价格、方向或期限值不合法。
    """

    side: Literal["buy", "sell"]
    _size: _SizeIntent
    limit: float | None = None
    stop: float | None = None
    sl: float | None = None
    tp: float | None = None
    expires_at: pd.Timestamp | None = None
    valid_bars: int | None = None
    _tag_json: str = field(default="null", repr=False)

    @overload
    def __init__(
        self,
        *,
        side: Literal["buy", "sell"],
        qty: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> None:
        """显式资产数量意图。"""

    @overload
    def __init__(
        self,
        *,
        side: Literal["buy", "sell"],
        amount: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> None:
        """显式名义金额意图，在提交时换算。"""

    @overload
    def __init__(
        self,
        *,
        side: Literal["buy", "sell"],
        percent: float,
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> None:
        """显式权益百分数意图，在提交时换算。"""

    def __init__(
        self,
        *,
        side: Literal["buy", "sell"],
        qty: float = cast(float, UNSET),
        amount: float = cast(float, UNSET),
        percent: float = cast(float, UNSET),
        limit: float | None = None,
        stop: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        tag: _JsonValue = None,
        expires_at: _Expiry | None = None,
        valid_bars: int | None = None,
    ) -> None:
        if side not in ("buy", "sell"):
            raise ValueError("side必须为buy/sell")
        size = select_size(qty=qty, amount=amount, percent=percent)
        values = _normalize_conditions(
            limit=limit,
            stop=stop,
            sl=sl,
            tp=tp,
            tag=tag,
            expires_at=expires_at,
            valid_bars=valid_bars,
        )
        values.pop("reduce_only")
        values["_tag_json"] = values.pop("tag_json")
        for name, value in (values | {"side": side, "_size": size}).items():
            object.__setattr__(self, name, value)

    @property
    def qty(self) -> float | None:
        """显式资产数量；其他模式返回 None。"""
        return self._size.value if self._size.mode == "qty" else None

    @property
    def amount(self) -> float | None:
        """显式名义金额；提交时换算，其他模式返回 None。"""
        return self._size.value if self._size.mode == "amount" else None

    @property
    def percent(self) -> float | None:
        """显式权益百分数（20 为20%）；其他模式返回 None。"""
        return self._size.value if self._size.mode == "percent" else None

    @property
    def tag(self) -> _JsonValue:
        """独立的 JSON 标签副本；修改副本不改变请求。"""
        return json.loads(self._tag_json)
