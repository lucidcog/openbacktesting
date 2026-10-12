"""ta.ht_trendmode: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.cycles.ht_trendmode import ht_trendmode as _calculate

from ..common import named_series


def compute(*, close, talib):
    result = _calculate(close=close, talib=talib)
    return named_series(result, "ta.ht_trendmode", "ht_trendmode")
