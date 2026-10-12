"""ta.midprice: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.midprice import midprice as _calculate

from ..common import named_series


def compute(*, high, low, length, talib):
    result = _calculate(high=high, low=low, length=length, talib=talib)
    return named_series(result, "ta.midprice", "midprice")
