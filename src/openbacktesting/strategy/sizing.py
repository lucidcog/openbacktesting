"""纯仓位预算：数量、净名义比例与计划止损风险。"""

from dataclasses import dataclass

from openbacktesting.broker.instrument import InstrumentSpec
from openbacktesting.broker.models import AccountSnapshot, finite


@dataclass(frozen=True)
class SizingDecision:
    """预算结果；estimated_cost为给定数量的成本估计，不保证成交价。"""

    qty: float
    reference_price: float
    estimated_cost: float
    reason: str | None
    budget: float | None = None


def _decision(qty, price, instrument, cost_per_unit, budget=None):
    price = finite(price, "reference_price", positive=True)
    cost = finite(cost_per_unit, "cost_per_unit")
    if cost < 0:
        raise ValueError("成本预算不得为负")
    qty = instrument.quantity(qty, floor=True)
    reason = None
    if qty == 0:
        reason = "below_min_quantity"
    elif qty * price < instrument.min_notional:
        qty, reason = 0.0, "below_min_notional"
    return SizingDecision(qty, price, qty * cost, reason, budget)


def fixed_quantity(qty: float, *, reference_price, instrument=None, cost_per_unit=0):
    """固定资产数量向零归整；不猜测资金比例。"""
    return _decision(qty, reference_price, instrument or InstrumentSpec(), cost_per_unit)


def equity_fraction(
    fraction, *, account: AccountSnapshot, reference_price, instrument=None, cost_per_unit=0
):
    """权益净名义预算，数量成本占用同一预算；保证金比例不放大此预算。"""
    equity = finite(account.equity, "equity", positive=True)
    fraction = finite(fraction, "fraction", positive=True)
    price = finite(reference_price, "reference_price", positive=True)
    cost = finite(cost_per_unit, "cost_per_unit")
    if cost < 0:
        raise ValueError("成本预算不得为负")
    budget = equity * fraction
    return _decision(budget / (price + cost), price, instrument or InstrumentSpec(), cost, budget)


def stop_risk(
    fraction,
    *,
    account: AccountSnapshot,
    reference_price,
    stop_price,
    side="buy",
    instrument=None,
    cost_per_unit=0,
):
    """止损风险预算含每单位往返成本估计；跳空可能超过计划损失。"""
    equity = finite(account.equity, "equity", positive=True)
    fraction = finite(fraction, "fraction", positive=True)
    price = finite(reference_price, "reference_price", positive=True)
    stop = finite(stop_price, "stop_price", positive=True)
    if (
        side not in ("buy", "sell")
        or (side == "buy" and stop >= price)
        or (side == "sell" and stop <= price)
    ):
        raise ValueError("止损方向或距离不合法")
    cost = finite(cost_per_unit, "cost_per_unit")
    if cost < 0:
        raise ValueError("成本预算不得为负")
    budget = equity * fraction
    return _decision(
        budget / (abs(price - stop) + cost), price, instrument or InstrumentSpec(), cost, budget
    )
