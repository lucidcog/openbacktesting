"""ta.avgprice: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.avgprice import avgprice as _calculate

from ..common import named_series


def compute(*, open_, high, low, close, talib):
    result = _calculate(open_=open_, high=high, low=low, close=close, talib=talib)
    return named_series(result, "ta.avgprice", "avgprice")
