"""ta.wma: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.wma import wma as _calculate

from ..common import named_series


def compute(*, close, length, asc, talib):
    result = _calculate(close=close, length=length, asc=asc, talib=talib)
    return named_series(result, "ta.wma", "wma")
