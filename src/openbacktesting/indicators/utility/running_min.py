"""ta.running_min: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source):
    return clean(source).cummin().rename("running_min")
