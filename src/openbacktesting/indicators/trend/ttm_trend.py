"""ta.ttm_trend：固定依赖的计算封装与规范输出。"""

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
