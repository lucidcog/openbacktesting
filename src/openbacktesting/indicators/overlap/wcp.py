"""ta.wcp：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.wcp import wcp as _calculate

from ..common import named_series


def compute(*, high, low, close, talib):
    result = _calculate(high=high, low=low, close=close, talib=talib)
    return named_series(result, "ta.wcp", "wcp")
