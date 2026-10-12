"""ta.range: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source, length):
    window = clean(source).rolling(length)
    return (window.max() - window.min()).rename("range")
