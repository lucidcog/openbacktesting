"""ta.vwma: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.vwma import vwma as _calculate

from ..common import named_series


def compute(*, close, volume, length, talib):
    result = _calculate(close=close, volume=volume, length=length, talib=talib)
    return named_series(result, "ta.vwma", "vwma")
