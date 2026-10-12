"""ta.vidya: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.vidya import vidya as _calculate

from ..common import named_series


def compute(*, close, length, drift, talib):
    result = _calculate(close=close, length=length, drift=drift, talib=talib)
    return named_series(result, "ta.vidya", "vidya")
