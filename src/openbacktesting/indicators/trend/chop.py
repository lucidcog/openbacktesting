"""ta.chop: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.chop import chop as _calculate

from ..common import named_series


def compute(*, high, low, close, length, atr_length, ln, scalar, drift, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        length=length,
        atr_length=atr_length,
        ln=ln,
        scalar=scalar,
        drift=drift,
        talib=talib,
    )
    return named_series(result, "ta.chop", "chop")
