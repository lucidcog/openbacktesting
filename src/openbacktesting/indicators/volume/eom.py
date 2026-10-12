"""ta.eom: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.eom import eom as _calculate

from ..common import named_series


def compute(*, high, low, close, volume, length, divisor, drift, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        volume=volume,
        length=length,
        divisor=divisor,
        drift=drift,
        talib=talib,
    )
    return named_series(result, "ta.eom", "eom")
