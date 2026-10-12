"""ta.ad: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.ad import ad as _calculate

from ..common import named_series


def compute(*, high, low, close, volume, open_, talib):
    result = _calculate(high=high, low=low, close=close, volume=volume, open_=open_, talib=talib)
    return named_series(result, "ta.ad", "ad")
