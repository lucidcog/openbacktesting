"""ta.mfi: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.mfi import mfi as _calculate

from ..common import named_series


def compute(*, high, low, close, volume, length, drift, talib):
    result = _calculate(
        high=high, low=low, close=close, volume=volume, length=length, drift=drift, talib=talib
    )
    return named_series(result, "ta.mfi", "mfi")
