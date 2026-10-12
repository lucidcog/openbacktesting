"""ta.decay: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.decay import decay as _calculate

from ..common import named_series


def compute(*, close, length, mode, kind, talib):
    result = _calculate(close=close, length=length, mode=mode, kind=kind, talib=talib)
    return named_series(result, "ta.decay", "decay")
