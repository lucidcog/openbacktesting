"""纯下单规模解析：意图不绑定运行，预算只使用显式提交上下文。"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from openbacktesting.broker.instrument import InstrumentSpec
from openbacktesting.broker.models import AccountSnapshot, OrderSizingSnapshot, finite


class _Unset(Enum):
    VALUE = "omitted"


UNSET = _Unset.VALUE


@dataclass(frozen=True)
class _SizeIntent:
    mode: Literal["qty", "amount", "percent"]
    value: float
    source: Literal["explicit", "default"] = "explicit"


def select_size(*, qty=UNSET, amount=UNSET, percent=UNSET, default=None, reduce_only=False):
    """校验规模选择；None 是显式非法值，只有全部省略才读取默认。"""
    if type(reduce_only) is not bool:
        raise TypeError("reduce_only必须为bool")
    supplied = [
        (mode, value)
        for mode, value in (("qty", qty), ("amount", amount), ("percent", percent))
        if value is not UNSET
    ]
    if len(supplied) > 1:
        raise TypeError("qty、amount、percent 必须互斥")
    if reduce_only and (not supplied or supplied[0][0] != "qty"):
        raise TypeError("只减仓必须显式提供 qty")
    if not supplied:
        if default is None:
            raise TypeError("必须提供 qty、amount、percent 之一或配置默认数量")
        return default
    mode, value = supplied[0]
    value = finite(value, mode, positive=True)
    if mode == "percent" and value > 100:
        raise ValueError("percent 必须在 (0,100]，20 表示 20%")
    return _SizeIntent(mode, value)


def resolve_size(
    intent: _SizeIntent,
    *,
    account: AccountSnapshot,
    reference_price: float,
    instrument: InstrumentSpec,
    reduce_only: bool = False,
) -> OrderSizingSnapshot:
    """按请求 Close 换算；显式数量严格校验，预算向零归整且不预留费用。"""
    price = finite(reference_price, "reference_price", positive=True)
    equity = finite(account.equity, "equity", positive=intent.mode == "percent")
    budget = None
    raw_qty = intent.value
    if intent.mode != "qty":
        budget = finite(
            equity * (intent.value / 100) if intent.mode == "percent" else intent.value,
            "budget",
            positive=True,
        )
        raw_qty = finite(budget / price, "预算数量", positive=True)
    floor = intent.mode != "qty" or intent.source == "default"
    qty = instrument.quantity(raw_qty, floor=floor, opening=not reduce_only)
    if floor:
        if qty == 0:
            raise ValueError("数量预算失败: below_min_quantity")
        if finite(qty * price, "预算名义金额") < instrument.min_notional:
            raise ValueError("数量预算失败: below_min_notional")
    return OrderSizingSnapshot(intent.mode, intent.source, intent.value, equity, price, budget, qty)
