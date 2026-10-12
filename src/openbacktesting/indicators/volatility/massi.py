"""ta.massi: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volatility.massi import massi as _calculate

from ..common import named_series


def compute(*, high, low, fast, slow, talib):
    result = _calculate(high=high, low=low, fast=fast, slow=slow, talib=talib)
    return named_series(result, "ta.massi", "massi")
