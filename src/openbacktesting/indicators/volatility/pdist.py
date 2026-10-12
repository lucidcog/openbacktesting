"""ta.pdist: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volatility.pdist import pdist as _calculate

from ..common import named_series


def compute(*, open_, high, low, close, drift, talib):
    result = _calculate(open_=open_, high=high, low=low, close=close, drift=drift, talib=talib)
    return named_series(result, "ta.pdist", "pdist")
