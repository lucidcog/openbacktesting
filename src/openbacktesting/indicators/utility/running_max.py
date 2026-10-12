"""ta.running_max: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source):
    return clean(source).cummax().rename("running_max")
