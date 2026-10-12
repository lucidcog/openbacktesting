"""ta.hvol: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volatility.hvol import hvol as _calculate

from ..common import named_series


def compute(*, close, length, annualization, talib):
    result = _calculate(close=close, length=length, annualization=annualization, talib=talib)
    return named_series(result, "ta.hvol", "hvol")
