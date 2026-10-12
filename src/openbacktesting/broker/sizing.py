"""Pure order-sizing resolution: intents are not bound to a run, and budgets use only explicit submission context."""

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
    """Validate sizing selection; None is explicitly invalid, and defaults apply only when all choices are omitted."""
    if type(reduce_only) is not bool:
        raise TypeError("reduce_only must be bool")
    supplied = [
        (mode, value)
        for mode, value in (("qty", qty), ("amount", amount), ("percent", percent))
        if value is not UNSET
    ]
    if len(supplied) > 1:
        raise TypeError("qty, amount, and percent are mutually exclusive")
    if reduce_only and (not supplied or supplied[0][0] != "qty"):
        raise TypeError("Reduce-only orders require an explicit qty")
    if not supplied:
        if default is None:
            raise TypeError("Supply one of qty, amount, or percent, or configure a default quantity")
        return default
    mode, value = supplied[0]
    value = finite(value, mode, positive=True)
    if mode == "percent" and value > 100:
        raise ValueError("percent must be in (0,100]; 20 means 20%")
    return _SizeIntent(mode, value)


def resolve_size(
    intent: _SizeIntent,
    *,
    account: AccountSnapshot,
    reference_price: float,
    instrument: InstrumentSpec,
    reduce_only: bool = False,
) -> OrderSizingSnapshot:
    """Convert using the requested Close; validate explicit quantity strictly and round budgets toward zero without reserving fees."""
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
        raw_qty = finite(budget / price, "Budgeted quantity", positive=True)
    floor = intent.mode != "qty" or intent.source == "default"
    qty = instrument.quantity(raw_qty, floor=floor, opening=not reduce_only)
    if floor:
        if qty == 0:
            raise ValueError("Quantity budget failed: below_min_quantity")
        if finite(qty * price, "Budgeted notional amount") < instrument.min_notional:
            raise ValueError("Quantity budget failed: below_min_notional")
    return OrderSizingSnapshot(intent.mode, intent.source, intent.value, equity, price, budget, qty)
