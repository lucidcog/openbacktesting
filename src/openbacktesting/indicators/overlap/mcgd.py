"""ta.mcgd: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.mcgd import mcgd as _calculate

from ..common import named_series


def compute(*, close, length, c, talib):
    result = _calculate(close=close, length=length, c=c, talib=talib)
    return named_series(result, "ta.mcgd", "mcgd")
