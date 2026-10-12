"""ta.roc: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.roc import roc as _calculate

from ..common import named_series


def compute(*, close, length, scalar, talib):
    result = _calculate(close=close, length=length, scalar=scalar, talib=talib)
    return named_series(result, "ta.roc", "roc")
