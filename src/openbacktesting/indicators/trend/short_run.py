"""ta.short_run: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.short_run import short_run as _calculate

from ..common import named_series


def compute(*, fast, slow, length, talib):
    result = _calculate(fast=fast, slow=slow, length=length, talib=talib)
    return named_series(result, "ta.short_run", "short_run")
