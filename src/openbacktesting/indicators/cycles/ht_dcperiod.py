"""ta.ht_dcperiod: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.cycles.ht_dcperiod import ht_dcperiod as _calculate

from ..common import named_series


def compute(*, close, talib):
    result = _calculate(close=close, talib=talib)
    return named_series(result, "ta.ht_dcperiod", "ht_dcperiod")
