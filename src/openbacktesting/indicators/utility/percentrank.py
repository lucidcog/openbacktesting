"""ta.percentrank: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source, length):
    return (100 * clean(source).rolling(length).rank(method="max", pct=True)).rename("percentrank")
