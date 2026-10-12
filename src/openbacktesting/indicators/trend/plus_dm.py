"""ta.plus_dm: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.plus_dm import plus_dm as _calculate

from ..common import named_series


def compute(*, high, low, length, drift, talib):
    result = _calculate(high=high, low=low, length=length, drift=drift, talib=talib)
    return named_series(result, "ta.plus_dm", "plus_dm")
