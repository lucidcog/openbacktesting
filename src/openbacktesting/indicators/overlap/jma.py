"""ta.jma: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.jma import jma as _calculate

from ..common import named_series


def compute(*, close, length, phase, talib):
    result = _calculate(close=close, length=length, phase=phase, talib=talib)
    return named_series(result, "ta.jma", "jma")
