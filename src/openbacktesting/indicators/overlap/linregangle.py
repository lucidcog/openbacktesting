"""ta.linregangle: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.linregangle import linregangle as _calculate

from ..common import named_series


def compute(*, close, length, talib):
    result = _calculate(close=close, length=length, talib=talib)
    return named_series(result, "ta.linregangle", "linregangle")
