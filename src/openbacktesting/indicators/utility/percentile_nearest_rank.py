"""ta.percentile_nearest_rank: Fixed causal sequence contract."""

from math import ceil

from ..calculus import clean


def compute(*, source, length, percentage):
    rank = max(0, ceil(percentage * length / 100) - 1)
    q = rank / max(1, length - 1)
    return (
        clean(source)
        .rolling(length)
        .quantile(q, interpolation="nearest")
        .rename("percentile_nearest_rank")
    )
