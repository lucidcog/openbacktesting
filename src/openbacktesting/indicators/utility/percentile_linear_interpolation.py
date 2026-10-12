"""ta.percentile_linear_interpolation：固定因果序列契约。"""

from ..calculus import clean


def compute(*, source, length, percentage):
    return (
        clean(source)
        .rolling(length)
        .quantile(percentage / 100)
        .rename("percentile_linear_interpolation")
    )
