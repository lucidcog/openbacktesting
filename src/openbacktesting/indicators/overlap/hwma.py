"""ta.hwma: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.hwma import hwma as _calculate

from ..common import named_series


def compute(*, close, na, nb, nc, talib):
    result = _calculate(close=close, na=na, nb=nb, nc=nc, talib=talib)
    return named_series(result, "ta.hwma", "hwma")
