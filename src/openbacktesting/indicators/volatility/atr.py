"""ta.atr: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volatility.atr import atr as _calculate

from ..common import named_series


def compute(*, high, low, close, length, mamode, drift, talib):
    result = _calculate(
        high=high, low=low, close=close, length=length, mamode=mamode, drift=drift, talib=talib
    )
    return named_series(result, "ta.atr", "atr")
