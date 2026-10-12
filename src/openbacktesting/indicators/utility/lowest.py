"""ta.lowest: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source, length):
    return clean(source).rolling(length).min().rename("lowest")
