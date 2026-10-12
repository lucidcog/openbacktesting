"""Pure position budgets: quantity, net-notional fraction, and planned stop-loss risk."""

from dataclasses import dataclass

from openbacktesting.broker.instrument import InstrumentSpec
from openbacktesting.broker.models import AccountSnapshot, finite


@dataclass(frozen=True)
class SizingDecision:
    """Budget result; estimated_cost estimates costs for the given quantity without guaranteeing fill prices."""

    qty: float
    reference_price: float
    estimated_cost: float
    reason: str | None
    budget: float | None = None


def _decision(qty, price, instrument, cost_per_unit, budget=None):
    price = finite(price, "reference_price", positive=True)
    cost = finite(cost_per_unit, "cost_per_unit")
    if cost < 0:
        raise ValueError("Cost budget must not be negative")
    qty = instrument.quantity(qty, floor=True)
    reason = None
    if qty == 0:
        reason = "below_min_quantity"
    elif qty * price < instrument.min_notional:
        qty, reason = 0.0, "below_min_notional"
    return SizingDecision(qty, price, qty * cost, reason, budget)


def fixed_quantity(qty: float, *, reference_price, instrument=None, cost_per_unit=0):
    """Round fixed asset quantities toward zero without inferring capital fractions."""
    return _decision(qty, reference_price, instrument or InstrumentSpec(), cost_per_unit)


def equity_fraction(
    fraction, *, account: AccountSnapshot, reference_price, instrument=None, cost_per_unit=0
):
    """Equity net-notional budget, with quantity costs charged to the same budget; margin fraction does not amplify it."""
    equity = finite(account.equity, "equity", positive=True)
    fraction = finite(fraction, "fraction", positive=True)
    price = finite(reference_price, "reference_price", positive=True)
    cost = finite(cost_per_unit, "cost_per_unit")
    if cost < 0:
        raise ValueError("Cost budget must not be negative")
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
    """Stop-loss risk budgets include estimated round-trip costs per unit; gaps may exceed the planned loss."""
    equity = finite(account.equity, "equity", positive=True)
    fraction = finite(fraction, "fraction", positive=True)
    price = finite(reference_price, "reference_price", positive=True)
    stop = finite(stop_price, "stop_price", positive=True)
    if (
        side not in ("buy", "sell")
        or (side == "buy" and stop >= price)
        or (side == "sell" and stop <= price)
    ):
        raise ValueError("Invalid stop-loss direction or distance")
    cost = finite(cost_per_unit, "cost_per_unit")
    if cost < 0:
        raise ValueError("Cost budget must not be negative")
    budget = equity * fraction
    return _decision(
        budget / (abs(price - stop) + cost), price, instrument or InstrumentSpec(), cost, budget
    )
