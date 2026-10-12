"""ta.zscore: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.statistics.zscore import zscore as _calculate

from ..common import named_series


def compute(*, close, length, std, talib):
    result = _calculate(close=close, length=length, std=std, talib=talib)
    return named_series(result, "ta.zscore", "zscore")
