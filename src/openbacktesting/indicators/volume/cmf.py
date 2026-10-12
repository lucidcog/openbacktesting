"""ta.cmf: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.cmf import cmf as _calculate

from ..common import named_series


def compute(*, high, low, close, volume, length, open_, talib):
    result = _calculate(
        high=high, low=low, close=close, volume=volume, length=length, open_=open_, talib=talib
    )
    return named_series(result, "ta.cmf", "cmf")
