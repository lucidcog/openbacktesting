"""ta.kama: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.kama import kama as _calculate

from ..common import named_series


def compute(*, close, length, fast, slow, drift, talib):
    result = _calculate(close=close, length=length, fast=fast, slow=slow, drift=drift, talib=talib)
    return named_series(result, "ta.kama", "kama")
