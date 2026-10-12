"""cdl_harami: Fixed native pattern with a separate validity mask."""

from pandas_ta_classic.candles.cdl_harami import cdl_harami as _calculate

from ..calculus import pattern_result


def compute(*, open_, high, low, close, talib):
    return pattern_result(
        _calculate,
        "cdl_harami",
        {"open_": open_, "high": high, "low": low, "close": close},
        12,
    )
