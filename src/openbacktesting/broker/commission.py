"""Reconstructible linear fee values without account or strategy state."""

from collections.abc import Mapping
from dataclasses import dataclass

from openbacktesting.broker.models import finite


@dataclass(frozen=True)
class Commission:
    """Fixed fee per fill, notional rate, and fee per asset unit; a rate of 0.002 means 0.2%."""

    fixed: float = 0.0
    relative: float = 0.0
    per_unit: float = 0.0

    def __post_init__(self):
        for name in ("fixed", "relative", "per_unit"):
            object.__setattr__(self, name, finite(getattr(self, name), f"commission_{name}"))
        if self.fixed < 0 or self.per_unit < 0 or not -0.1 <= self.relative < 0.1:
            raise ValueError("Commission configuration is outside the allowed range")

    def calculate(self, qty: float, price: float) -> float:
        """Calculate fees from actual fill quantity and price; the caller validates fill values."""
        return self.fixed + abs(qty) * price * self.relative + abs(qty) * self.per_unit

    def snapshot(self) -> dict:
        """Export independent plain values with a model version."""
        return {
            "kind": "linear",
            "version": 1,
            "fixed": self.fixed,
            "relative": self.relative,
            "per_unit": self.per_unit,
        }

    @classmethod
    def from_snapshot(cls, value: Mapping) -> "Commission":
        """Restore a complete snapshot strictly; reject unknown versions, fields, and implicit defaults."""
        if not isinstance(value, Mapping):
            raise TypeError("Commission snapshot must be a mapping")
        if set(value) != {"kind", "version", "fixed", "relative", "per_unit"}:
            raise ValueError("Commission snapshot has missing or unknown fields")
        if value["kind"] != "linear" or type(value["version"]) is not int or value["version"] != 1:
            raise ValueError("Unsupported Commission snapshot model or version")
        return cls(value["fixed"], value["relative"], value["per_unit"])


def normalize_commission(value: float | tuple[float, float] | Commission) -> Commission:
    """Normalize legacy fee inputs to a plain-value model; callables are not accepted."""
    if isinstance(value, Commission):
        return value
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError("commission tuple must contain a fixed fee and a rate")
        return Commission(fixed=value[0], relative=value[1])
    return Commission(relative=value)
