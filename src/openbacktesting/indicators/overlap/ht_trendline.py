"""ta.ht_trendline: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.ht_trendline import ht_trendline as _calculate

from ..common import named_series


def compute(*, close, talib):
    result = _calculate(close=close, talib=talib)
    return named_series(result, "ta.ht_trendline", "ht_trendline")
