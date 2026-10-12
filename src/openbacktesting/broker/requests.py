"""Author-supplied order descriptions and public argument validation without trading side effects."""

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
    """Normalize conditions requiring no account or instrument; do not modify caller data."""
    if type(reduce_only) is not bool:
        raise TypeError("reduce_only must be bool")
    prices = {
        name: None if value is None else finite(value, name, positive=True)
        for name, value in (("limit", limit), ("stop", stop), ("sl", sl), ("tp", tp))
    }
    if expires_at is not None and valid_bars is not None:
        raise ValueError("expires_at and valid_bars are mutually exclusive")
    if valid_bars is not None and (
        isinstance(valid_bars, bool) or not isinstance(valid_bars, int) or valid_bars <= 0
    ):
        raise ValueError("valid_bars must be a positive integer")
    if expires_at is not None:
        if not isinstance(expires_at, (datetime, pd.Timestamp, str)):
            raise TypeError("expires_at must be a timezone-aware timestamp or string")
        expires_at = pd.Timestamp(expires_at)
        if pd.isna(expires_at):
            raise ValueError("expires_at must not be NaT")
        if expires_at.tzinfo is None:
            raise ValueError("Absolute expiration must be timezone-aware")
    return prices | {
        "reduce_only": reduce_only,
        "expires_at": expires_at,
        "valid_bars": valid_bars,
        "tag_json": freeze_tag(tag),
    }


@dataclass(frozen=True, init=False)
class OrderRequest:
    """Frozen entry request awaiting submission; construction does not register an order and is allowed during initialization.

    All arguments must be supplied by name. Instrument precision, market-data timezone, and protection direction are validated at submission.
    ``tag`` supports plain JSON values; it is frozen at construction, and reads return independent copies.

    Args:
        side: Buy (buy) or sell (sell).
        qty: Finite positive asset quantity; choose exactly one of qty/amount/percent, without using a default budget.
        amount: Finite positive notional amount, converted using Close at submission without reserving fees.
        percent: Equity percentage in (0,100]; 20 means 20%, calculated at submission.
        limit: Entry limit price; None means no limit condition.
        stop: Entry trigger price, distinct from the post-entry sl.
        sl: Absolute post-entry stop-loss price.
        tp: Absolute post-entry take-profit price.
        tag: Optional user tag, excluded from matching conditions.
        expires_at: Timezone-aware absolute expiration, mutually exclusive with valid_bars.
        valid_bars: Number of bars eligible for execution after submission; must be a positive integer.

    Raises:
        TypeError: Invalid argument types, names, or tag types.
        ValueError: Invalid quantity, price, direction, or expiration values.
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
        """Explicit asset-quantity intent."""

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
        """Explicit notional-amount intent, converted at submission."""

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
        """Explicit equity-percentage intent, converted at submission."""

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
            raise ValueError("side must be buy/sell")
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
        """Explicit asset quantity; None in other modes."""
        return self._size.value if self._size.mode == "qty" else None

    @property
    def amount(self) -> float | None:
        """Explicit notional amount; converted at submission, None in other modes."""
        return self._size.value if self._size.mode == "amount" else None

    @property
    def percent(self) -> float | None:
        """Explicit equity percentage (20 means 20%); None in other modes."""
        return self._size.value if self._size.mode == "percent" else None

    @property
    def tag(self) -> _JsonValue:
        """Independent JSON tag copy; modifying it does not change the request."""
        return json.loads(self._tag_json)
