"""Explicit asset units; trading rules are not inferred from market-data decimal places."""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR, ROUND_HALF_UP, Decimal, localcontext

import numpy as np

from openbacktesting.broker.models import finite


@dataclass(frozen=True)
class InstrumentSpec:
    """Actual asset quantity and price grids; currency is only a label."""

    symbol: str = "asset"
    quantity_step: float = 1
    min_quantity: float | None = None
    price_tick: float | None = None
    min_notional: float = 0
    currency: str | None = None

    def __post_init__(self):
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("symbol must be a nonempty string")
        if self.currency is not None and not isinstance(self.currency, str):
            raise TypeError("currency must be a string or None")
        step = finite(self.quantity_step, "quantity_step", positive=True)
        minimum = (
            step
            if self.min_quantity is None
            else finite(self.min_quantity, "min_quantity", positive=True)
        )
        object.__setattr__(self, "quantity_step", step)
        object.__setattr__(self, "min_quantity", minimum)
        if self.price_tick is not None:
            object.__setattr__(
                self, "price_tick", finite(self.price_tick, "price_tick", positive=True)
            )
        object.__setattr__(self, "min_notional", finite(self.min_notional, "min_notional"))
        if self.min_notional < 0:
            raise ValueError("min_notional must not be negative")

    def quantity(self, value, *, floor=False, opening=True) -> float:
        """Direct requests must lie on the grid; budgeted quantities may round toward zero."""
        value = finite(value, "qty")
        if value < 0:
            raise ValueError("qty must not be negative")
        lots = Decimal(str(value)) / Decimal(str(self.quantity_step))
        whole = lots.to_integral_value(rounding=ROUND_DOWN)
        if not floor and lots != whole:
            raise ValueError("qty is not on the quantity_step grid")
        result = float(whole * Decimal(str(self.quantity_step)))
        if opening and result < self.min_quantity:
            if floor:
                return 0.0
            raise ValueError("qty is below min_quantity")
        return result

    def price(self, value, *, side=None) -> float:
        """Validate requested prices strictly; normalize execution prices in the adverse direction."""
        value = finite(value, "price", positive=True)
        if self.price_tick is None:
            return value
        ticks = Decimal(str(value)) / Decimal(str(self.price_tick))
        rounded = ticks.to_integral_value(rounding=ROUND_CEILING if side == "buy" else ROUND_FLOOR)
        if side is None and ticks != rounded:
            raise ValueError("price is not on the price_tick grid")
        return float(rounded * Decimal(str(self.price_tick)))

    def validate_data(self, frame):
        """Trading market data must be ordered, unique, and have valid prices; explicit ticks must not be silently corrected."""
        if not frame.index.is_monotonic_increasing or not frame.index.is_unique:
            raise ValueError("Market-data index must be increasing and unique")
        values = frame[["Open", "High", "Low", "Close"]].to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError("OHLC must contain finite positive prices")
        if self.price_tick is not None:
            for price in np.unique(values):
                self.price(float(price))

    def round_price_to_tick(self, value: float) -> float:
        """Round prices to the nearest explicit tick; half ticks round to the higher price.

        Args:
            value: Finite positive price; booleans are not accepted.

        Returns:
            Finite positive float passing this instrument's strict grid validation; does not change matching-rounding policy.

        Raises:
            TypeError: value is nonnumeric or a boolean.
            ValueError: Missing tick, invalid input, zero result, or a valid grid value cannot be represented as a float.
        """
        value = finite(value, "price", positive=True)
        if self.price_tick is None:
            raise ValueError("round_price_to_tick requires an explicit price_tick")
        # Decimal exponents of two finite floats can differ by more than 600; prevent default precision from losing half ticks.
        with localcontext() as context:
            context.prec = 700
            tick = Decimal(str(self.price_tick))
            ticks = (Decimal(str(value)) / tick).to_integral_value(rounding=ROUND_HALF_UP)
            exact = ticks * tick
            result = float(exact)
            if Decimal(str(result)) != exact:
                raise ValueError("Rounded price cannot represent the grid exactly as a float")
            return self.price(result)
