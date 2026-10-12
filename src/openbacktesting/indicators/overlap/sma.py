"""ta.sma: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.sma import sma as _calculate

from ..common import named_series


def compute(*, close, length, offset, talib):
    result = _calculate(close=close, length=length, offset=offset, talib=talib)
    return named_series(result, "ta.sma", "sma")


def compute_pandas(*, close, length, offset):
    return close.rolling(length, min_periods=length).mean().shift(offset).rename("sma")
