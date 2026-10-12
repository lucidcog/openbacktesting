"""ta.correl: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.statistics.correl import correl as _calculate

from ..common import named_series


def compute(*, close, benchmark, length, talib):
    result = _calculate(close=close, benchmark=benchmark, length=length, talib=talib)
    return named_series(result, "ta.correl", "correl")
