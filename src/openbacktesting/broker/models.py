"""Trade requests, events, and accounting snapshots independent of strategies and execution loops."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from enum import StrEnum
from functools import cache
from math import isfinite
from numbers import Real
from typing import Literal


def finite(value, name: str, *, positive=False) -> float:
    """Reject booleans, nonnumeric values, and nonfinite values; return a normalized number."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a finite number")
    value = float(value)
    if not isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{name} must be a {'positive ' if positive else ''}finite number")
    return value


class OrderStatus(StrEnum):
    """Observable order states; terminal states cannot reopen."""

    SUBMITTED = "Submitted"
    ACCEPTED = "Accepted"
    PARTIALLY_FILLED = "PartiallyFilled"
    FILLED = "Filled"
    CANCELED = "Canceled"
    EXPIRED = "Expired"
    REJECTED = "Rejected"

    @property
    def terminal(self) -> bool:
        """Whether the state is terminal."""
        return self in (self.FILLED, self.CANCELED, self.EXPIRED, self.REJECTED)


@dataclass(frozen=True)
class ClosedTradeStats:
    """Cumulative closed portions as of the read; fees are allocated, and unrealized profit or loss is excluded.

    Count closed portions rather than trade_id values; classify wins and losses by strictly positive or negative net profit or loss.
    losing_amount is a nonnegative loss amount; average net profit or loss and the 0–1 win rate are None for empty records.
    Values contain no runtime objects; saved snapshots are unaffected by later fills.
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
    """Sizing basis frozen at submission; budgets do not guarantee actual fill notional or fees.

    mode is qty/amount/percent, source is explicit/default; percent value
    uses percentage points (20 means 20%), and budget is None in qty mode.
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
    """Immutable normalized request; tag is stored as JSON text, and reads return independent plain values."""

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
        """Return an independent tag copy; modifying it does not change the request."""
        return json.loads(self.tag_json)


@dataclass(frozen=True)
class OrderSnapshot:
    """Frozen order values at a state transition."""

    order_id: str
    status: OrderStatus
    filled_qty: float
    remaining_qty: float
    avg_fill_price: float | None
    reason: str | None
    triggered: bool


@dataclass(frozen=True)
class OrderEvent:
    """Immutable order event with time and phase."""

    sequence: int
    bar_index: int
    timestamp: object
    phase: str
    snapshot: OrderSnapshot


@dataclass(frozen=True)
class Fill:
    """An actual execution; fees are recorded exactly once here."""

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
    """Allocation of an execution quantity to entry lots or closed portions."""

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
    """Single-currency linear margin account; balance is not securities settlement cash."""

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
    """Net position, two-sided gross exposure, and explicit gross and net profit or loss."""

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
        """A two-sided net-zero position still has gross exposure."""
        return self.gross_qty > 0


@dataclass(frozen=True)
class RunSummary:
    """Frozen summary for the finish hook; error text does not replace the original exception."""

    reason: str
    account: AccountSnapshot
    error: str | None = None


def record(value) -> dict:
    """Produce a value-only dictionary without exposing live trading objects."""
    names = _field_names(type(value))
    return dict(zip(names, map(value.__dict__.__getitem__, names)))


def columns(model) -> list[str]:
    """Empty result tables retain model fields."""
    return list(_field_names(model))


@cache
def _field_names(model):
    return tuple(item.name for item in fields(model))


def freeze_tag(value) -> str:
    """Freeze JSON-safe tags as text; reject nonstring keys and nonfinite numbers."""

    def validate(item):
        if isinstance(item, dict):
            if not all(isinstance(key, str) for key in item):
                raise TypeError("tag mapping keys must be strings")
            for child in item.values():
                validate(child)
        elif isinstance(item, list):
            for child in item:
                validate(child)
        elif item is not None and not isinstance(item, (str, bool, int, float)):
            raise TypeError("tag supports only plain JSON values")

    validate(value)
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)
