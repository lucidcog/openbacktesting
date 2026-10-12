"""ta.ma: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.ma import ma as _calculate

from ..common import named_series


def compute(*, source, name, length, talib):
    result = _calculate(source=source, name=name, length=length, talib=talib)
    return named_series(result, "ta.ma", "ma")
