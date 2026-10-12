"""ta.dx: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.dx import dx as _calculate

from ..common import named_series


def compute(*, high, low, close, length, scalar, mamode, drift, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        length=length,
        scalar=scalar,
        mamode=mamode,
        drift=drift,
        talib=talib,
    )
    return named_series(result, "ta.dx", "dx")
