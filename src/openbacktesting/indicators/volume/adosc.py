"""ta.adosc: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.adosc import adosc as _calculate

from ..common import named_series


def compute(*, high, low, close, volume, fast, slow, open_, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        volume=volume,
        fast=fast,
        slow=slow,
        open_=open_,
        talib=talib,
    )
    return named_series(result, "ta.adosc", "adosc")
