"""ta.percent_return: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.performance.percent_return import percent_return as _calculate

from ..common import named_series


def compute(*, close, length, cumulative, talib):
    result = _calculate(close=close, length=length, cumulative=cumulative, talib=talib)
    return named_series(result, "ta.percent_return", "percent_return")
