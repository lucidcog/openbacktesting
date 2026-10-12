"""ta.decreasing: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.decreasing import decreasing as _calculate

from ..common import named_series


def compute(*, close, length, strict, asint, percent, drift, talib):
    result = _calculate(
        close=close,
        length=length,
        strict=strict,
        asint=asint,
        percent=percent,
        drift=drift,
        talib=talib,
    )
    return named_series(result, "ta.decreasing", "decreasing")
