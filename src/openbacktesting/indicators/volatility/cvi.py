"""ta.cvi: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volatility.cvi import cvi as _calculate

from ..common import named_series


def compute(*, high, low, length, talib):
    result = _calculate(high=high, low=low, length=length, talib=talib)
    return named_series(result, "ta.cvi", "cvi")
