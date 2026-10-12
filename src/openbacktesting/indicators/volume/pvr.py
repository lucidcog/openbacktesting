"""ta.pvr: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.pvr import pvr as _calculate

from ..common import named_series


def compute(*, close, volume, talib):
    result = _calculate(close=close, volume=volume, talib=talib)
    return named_series(result, "ta.pvr", "pvr")
