"""ta.ohlc4: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.ohlc4 import ohlc4 as _calculate

from ..common import named_series


def compute(*, open_, high, low, close, talib):
    result = _calculate(open_=open_, high=high, low=low, close=close, talib=talib)
    return named_series(result, "ta.ohlc4", "ohlc4")
