"""交易请求、事件与会计快照；均不依赖策略或执行循环。"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from enum import StrEnum
from functools import cache
from math import isfinite
from numbers import Real
from typing import Literal


def finite(value, name: str, *, positive=False) -> float:
    """拒绝布尔、非数值和非有限值，返回规范化数值。"""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} 必须为有限数值")
    value = float(value)
    if not isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{name} 必须为{'正' if positive else ''}有限数值")
    return value


class OrderStatus(StrEnum):
    """订单可观察状态；终态不可重新打开。"""

    SUBMITTED = "Submitted"
    ACCEPTED = "Accepted"
    PARTIALLY_FILLED = "PartiallyFilled"
    FILLED = "Filled"
    CANCELED = "Canceled"
    EXPIRED = "Expired"
    REJECTED = "Rejected"

    @property
    def terminal(self) -> bool:
        """是否已终结。"""
        return self in (self.FILLED, self.CANCELED, self.EXPIRED, self.REJECTED)


@dataclass(frozen=True)
class ClosedTradeStats:
    """截至读取时的关闭片段累计；费用已分摊，不含未平仓损益。

    次数按关闭片段而非 trade_id 计数，胜负按净损益严格正负分类。
    losing_amount 是非负亏损额；空记录的平均净损益和 0–1 胜率为 None。
    值不携带运行对象，保存的快照不受后续成交影响。
    """

    closed_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    even_count: int = 0
    winning_profit: float = 0.0
    losing_amount: float = 0.0
    net_profit: float = 0.0
    average_profit: float | None = None
    win_rate: float | None = None


@dataclass(frozen=True)
class OrderSizingSnapshot:
    """提交时冻结的规模依据；预算不保证真实成交金额或费用。

    mode 为 qty/amount/percent，source 为 explicit/default；percent 的 value
    使用百分数（20 表示 20%），qty 模式的 budget 为 None。
    """

    mode: Literal["qty", "amount", "percent"]
    source: Literal["explicit", "default"]
    value: float
    equity: float
    reference_price: float
    budget: float | None
    qty: float


@dataclass(frozen=True)
class NormalizedOrderRequest:
    """不可变规范化请求；tag以JSON文本保存，读取返回独立纯值。"""

    side: str
    qty: float
    limit: float | None = None
    stop: float | None = None
    sl: float | None = None
    tp: float | None = None
    reduce_only: bool = False
    trade_id: str | None = None
    expires_at: object = None
    valid_bars: int | None = None
    tag_json: str = "null"

    @property
    def tag(self):
        """返回独立标签副本，修改副本不会改变请求。"""
        return json.loads(self.tag_json)


@dataclass(frozen=True)
class OrderSnapshot:
    """订单在某次状态迁移时的冻结值。"""

    order_id: str
    status: OrderStatus
    filled_qty: float
    remaining_qty: float
    avg_fill_price: float | None
    reason: str | None
    triggered: bool


@dataclass(frozen=True)
class OrderEvent:
    """带时间和阶段的不可变订单事件。"""

    sequence: int
    bar_index: int
    timestamp: object
    phase: str
    snapshot: OrderSnapshot


@dataclass(frozen=True)
class Fill:
    """一次实际执行，费用只在此处记账一次。"""

    fill_id: str
    order_id: str
    sequence: int
    side: str
    qty: float
    price: float
    fee: float
    bar_index: int
    timestamp: object
    phase: str
    reason: str


@dataclass(frozen=True)
class TradeAllocation:
    """执行量在开仓批次或关闭片段上的分配。"""

    allocation_id: str
    fill_id: str
    trade_id: str
    entry_fill_id: str
    kind: str
    qty: float
    fee: float
    entry_fee: float
    realized_pnl_gross: float


@dataclass(frozen=True)
class AccountSnapshot:
    """单币种线性保证金账户，balance并非证券交收现金。"""

    balance: float
    equity: float
    realized_pnl_gross: float
    unrealized_pnl_gross: float
    fees_paid: float
    margin_used: float
    margin_available: float
    gross_notional: float
    net_notional: float


@dataclass(frozen=True)
class PositionSnapshot:
    """净仓、双向总暴露与明确毛净损益。"""

    net_qty: float
    gross_qty: float
    long_qty: float
    short_qty: float
    long_avg_price: float | None
    short_avg_price: float | None
    avg_price: float | None
    gross_notional: float
    net_notional: float
    unrealized_pnl_gross: float
    unrealized_pnl_net: float
    entry_fees_remaining: float
    return_fraction: float | None

    @property
    def has_exposure(self) -> bool:
        """双向净零仓仍有总暴露。"""
        return self.gross_qty > 0


@dataclass(frozen=True)
class RunSummary:
    """结束钩子的冻结摘要；错误信息不替代原异常。"""

    reason: str
    account: AccountSnapshot
    error: str | None = None


def record(value) -> dict:
    """生成仅含值的字典；不暴露活交易对象。"""
    names = _field_names(type(value))
    return dict(zip(names, map(value.__dict__.__getitem__, names)))


def columns(model) -> list[str]:
    """空结果表仍保留模型字段。"""
    return list(_field_names(model))


@cache
def _field_names(model):
    return tuple(item.name for item in fields(model))


def freeze_tag(value) -> str:
    """将JSON安全标签固化为文本，拒绝非字符串键与非有限数。"""

    def validate(item):
        if isinstance(item, dict):
            if not all(isinstance(key, str) for key in item):
                raise TypeError("tag 映射键必须为字符串")
            for child in item.values():
                validate(child)
        elif isinstance(item, list):
            for child in item:
                validate(child)
        elif item is not None and not isinstance(item, (str, bool, int, float)):
            raise TypeError("tag 仅支持JSON纯值")

    validate(value)
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)
