"""ta.ttm_trend: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.ttm_trend import ttm_trend as _calculate

from ..common import named_frame


def compute(*, high, low, close, length, talib):
    result = _calculate(high=high, low=low, close=close, length=length, talib=talib)
    return named_frame(
        result,
        "ta.ttm_trend",
        {
            f"TTM_TRND_{length}": "ttm_trend",
        },
    )
