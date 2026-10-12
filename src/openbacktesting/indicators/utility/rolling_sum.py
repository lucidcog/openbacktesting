"""ta.rolling_sum: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source, length):
    return clean(source).rolling(length).sum().rename("rolling_sum")
