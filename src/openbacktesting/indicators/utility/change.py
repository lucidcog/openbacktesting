"""ta.change: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source, length):
    return clean(source).diff(length).rename("change")
