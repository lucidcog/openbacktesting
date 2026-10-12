"""ta.mavp: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.mavp import mavp as _calculate

from ..common import named_series


def compute(*, close, periods, minperiod, maxperiod, mamode, talib):
    result = _calculate(
        close=close,
        periods=periods,
        minperiod=minperiod,
        maxperiod=maxperiod,
        mamode=mamode,
        talib=talib,
    )
    return named_series(result, "ta.mavp", "mavp")
