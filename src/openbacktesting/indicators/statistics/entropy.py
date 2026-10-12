"""ta.entropy: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.statistics.entropy import entropy as _calculate

from ..common import named_series


def compute(*, close, length, base, talib):
    result = _calculate(close=close, length=length, base=base, talib=talib)
    return named_series(result, "ta.entropy", "entropy")
