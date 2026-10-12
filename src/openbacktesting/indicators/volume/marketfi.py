"""ta.marketfi: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.marketfi import marketfi as _calculate

from ..common import named_series


def compute(*, high, low, volume, talib):
    result = _calculate(high=high, low=low, volume=volume, talib=talib)
    return named_series(result, "ta.marketfi", "marketfi")
