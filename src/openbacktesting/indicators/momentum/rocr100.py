"""ta.rocr100: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.rocr100 import rocr100 as _calculate

from ..common import named_series


def compute(*, close, length, talib):
    result = _calculate(close=close, length=length, talib=talib)
    return named_series(result, "ta.rocr100", "rocr100")
