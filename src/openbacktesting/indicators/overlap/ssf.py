"""ta.ssf: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.ssf import ssf as _calculate

from ..common import named_series


def compute(*, close, length, poles, talib):
    result = _calculate(close=close, length=length, poles=poles, talib=talib)
    return named_series(result, "ta.ssf", "ssf")
