"""ta.ebsw: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.cycles.ebsw import ebsw as _calculate

from ..common import named_series


def compute(*, close, length, bars, talib):
    result = _calculate(close=close, length=length, bars=bars, talib=talib)
    return named_series(result, "ta.ebsw", "ebsw")
