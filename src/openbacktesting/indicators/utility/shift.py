"""ta.shift: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source, length):
    return clean(source).shift(length).rename("shift")
