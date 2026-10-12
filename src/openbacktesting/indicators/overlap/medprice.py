"""ta.medprice: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.medprice import medprice as _calculate

from ..common import named_series


def compute(*, high, low, talib):
    result = _calculate(high=high, low=low, talib=talib)
    return named_series(result, "ta.medprice", "medprice")
