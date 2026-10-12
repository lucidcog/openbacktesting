"""ta.willr: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.willr import willr as _calculate

from ..common import named_series


def compute(*, high, low, close, length, talib):
    result = _calculate(high=high, low=low, close=close, length=length, talib=talib)
    return named_series(result, "ta.willr", "willr")
