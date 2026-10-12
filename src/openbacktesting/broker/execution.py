"""Independent deterministic OHLC fill-price policy."""

from dataclasses import dataclass

from openbacktesting.broker.models import finite


@dataclass(frozen=True)
class Slippage:
    """No slippage, fixed-price slippage, or basis-point slippage; apply once per fill."""

    mode: str = "none"
    value: float = 0

    def __post_init__(self):
        if self.mode not in ("none", "fixed", "bps"):
            raise ValueError("slippage mode must be none/fixed/bps")
        object.__setattr__(self, "value", finite(self.value, "slippage"))
        if self.value < 0 or (self.mode == "none" and self.value != 0):
            raise ValueError("Invalid slippage value")

    def cost(self, price: float) -> float:
        """Return a nonnegative slippage distance per unit."""
        if self.mode == "fixed":
            return self.value
        return price * self.value / 10000 if self.mode == "bps" else 0.0


def match_price(request, *, triggered, open_, high, low):
    """Return the candidate reference price and trigger state without modifying the request."""
    buy = request.side == "buy"
    stop = request.stop if not triggered else None
    if stop is not None:
        if not (high >= stop if buy else low <= stop):
            return None, False
        triggered = True
    if request.limit is not None:
        limit = request.limit
        if not (low <= limit if buy else high >= limit):
            return None, triggered
        if stop is not None and (limit <= stop if buy else limit >= stop):
            return None, triggered
        return (min(stop or open_, limit) if buy else max(stop or open_, limit)), triggered
    return ((max(open_, stop) if buy else min(open_, stop)) if stop else open_), triggered


def execution_price(base, side, *, spread, slippage, instrument, limit, bounds=None):
    """Apply costs and the grid before checking the limit; ordinary execution is constrained to the OHLC range."""
    sign = 1 if side == "buy" else -1
    price = base * (1 + sign * spread) + sign * slippage.cost(base)
    price = instrument.price(price, side=side)
    if limit is not None and (price > limit if side == "buy" else price < limit):
        return None
    if bounds is not None:
        low, high = bounds
        price = min(max(price, low), high)
        price = instrument.price(price, side=side)
        if not low <= price <= high:
            return None
    if limit is not None and (price > limit if side == "buy" else price < limit):
        return None
    return price
