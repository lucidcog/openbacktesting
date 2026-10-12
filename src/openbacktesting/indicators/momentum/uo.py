"""ta.uo：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.uo import uo as _calculate

from ..common import named_series


def compute(*, high, low, close, fast, medium, slow, fast_w, medium_w, slow_w, drift, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        fast=fast,
        medium=medium,
        slow=slow,
        fast_w=fast_w,
        medium_w=medium_w,
        slow_w=slow_w,
        drift=drift,
        talib=talib,
    )
    return named_series(result, "ta.uo", "uo")
