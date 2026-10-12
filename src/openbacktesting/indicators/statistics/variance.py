"""ta.variance: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.statistics.variance import variance as _calculate

from ..common import named_series


def compute(*, close, length, ddof, talib):
    result = _calculate(close=close, length=length, ddof=ddof, talib=talib)
    return named_series(result, "ta.variance", "variance")
