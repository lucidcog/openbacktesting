"""ta.vwap: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.vwap import vwap as _calculate

from ..common import named_series


def compute(*, high, low, close, volume, anchor, talib):
    result = _calculate(high=high, low=low, close=close, volume=volume, anchor=anchor, talib=talib)
    return named_series(result, "ta.vwap", "vwap")
