"""cdl_shootingstar: Fixed native pattern with a separate validity mask."""

from pandas_ta_classic.candles.cdl_shootingstar import cdl_shootingstar as _calculate

from ..calculus import pattern_result


def compute(*, open_, high, low, close, talib):
    return pattern_result(
        _calculate,
        "cdl_shootingstar",
        {"open_": open_, "high": high, "low": low, "close": close},
        12,
    )
