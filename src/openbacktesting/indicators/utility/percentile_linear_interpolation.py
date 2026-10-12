"""ta.percentile_linear_interpolation: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source, length, percentage):
    return (
        clean(source)
        .rolling(length)
        .quantile(percentage / 100)
        .rename("percentile_linear_interpolation")
    )
