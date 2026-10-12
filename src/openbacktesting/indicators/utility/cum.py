"""ta.cum: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source):
    return clean(source).cumsum().rename("cum")
