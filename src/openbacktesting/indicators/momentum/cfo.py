"""ta.cfo: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.cfo import cfo as _calculate

from ..common import named_series


def compute(*, close, length, scalar, drift, talib):
    result = _calculate(close=close, length=length, scalar=scalar, drift=drift, talib=talib)
    return named_series(result, "ta.cfo", "cfo")
