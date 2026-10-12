"""ta.log_return: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.performance.log_return import log_return as _calculate

from ..common import named_series


def compute(*, close, length, cumulative, talib):
    result = _calculate(close=close, length=length, cumulative=cumulative, talib=talib)
    return named_series(result, "ta.log_return", "log_return")
