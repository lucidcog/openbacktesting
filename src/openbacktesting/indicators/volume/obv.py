"""ta.obv: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.obv import obv as _calculate

from ..common import named_series


def compute(*, close, volume, talib):
    result = _calculate(close=close, volume=volume, talib=talib)
    return named_series(result, "ta.obv", "obv")
