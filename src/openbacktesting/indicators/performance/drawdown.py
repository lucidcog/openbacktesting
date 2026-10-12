"""ta.drawdown: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.performance.drawdown import drawdown as _calculate

from ..common import named_frame


def compute(*, close, talib):
    result = _calculate(close=close, talib=talib)
    return named_frame(
        result,
        "ta.drawdown",
        {
            "DD": "absolute",
            "DD_PCT": "percent",
            "DD_LOG": "logarithmic",
        },
    )
