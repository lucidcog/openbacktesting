"""ta.t3: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.t3 import t3 as _calculate

from ..common import named_series


def compute(*, close, length, a, talib):
    result = _calculate(close=close, length=length, a=a, talib=talib)
    return named_series(result, "ta.t3", "t3")
