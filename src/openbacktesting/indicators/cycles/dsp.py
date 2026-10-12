"""ta.dsp: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.cycles.dsp import dsp as _calculate

from ..common import named_series


def compute(*, close, length, talib):
    result = _calculate(close=close, length=length, talib=talib)
    return named_series(result, "ta.dsp", "dsp")
