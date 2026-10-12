"""ta.stdev: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.statistics.stdev import stdev as _calculate

from ..common import named_series


def compute(*, close, length, ddof, talib):
    result = _calculate(close=close, length=length, ddof=ddof, talib=talib)
    return named_series(result, "ta.stdev", "stdev")
