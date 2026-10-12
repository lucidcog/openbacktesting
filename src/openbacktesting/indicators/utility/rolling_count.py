"""ta.rolling_count: Fixed causal sequence contract."""

from ..calculus import condition as validate_condition


def compute(*, condition, length):
    return (
        validate_condition(condition, "ta.rolling_count")
        .rolling(length)
        .sum()
        .rename("rolling_count")
    )
