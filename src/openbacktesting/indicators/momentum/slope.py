"""ta.slope: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.slope import slope as _calculate

from ..common import named_series


def compute(*, close, length, as_angle, to_degrees, vertical, talib):
    result = _calculate(
        close=close,
        length=length,
        as_angle=as_angle,
        to_degrees=to_degrees,
        vertical=vertical,
        talib=talib,
    )
    return named_series(result, "ta.slope", "slope")
