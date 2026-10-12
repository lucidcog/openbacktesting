"""ta.rolling_count：固定因果序列契约。"""

from ..calculus import condition as validate_condition


def compute(*, condition, length):
    return (
        validate_condition(condition, "ta.rolling_count")
        .rolling(length)
        .sum()
        .rename("rolling_count")
    )
