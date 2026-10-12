"""Pure numeric validation of statistical rates without runtime or account dependencies."""

from math import isfinite
from numbers import Real


def validate_risk_free_rate(value: float) -> float:
    """Accept annualized fractions; reject booleans, nonfinite values, and out-of-range values."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("risk_free_rate must be a finite number")
    value = float(value)
    if not isfinite(value) or not -1 < value < 1:
        raise ValueError("risk_free_rate must be in (-1, 1)")
    return value
