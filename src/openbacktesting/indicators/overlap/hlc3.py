"""ta.hlc3：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.hlc3 import hlc3 as _calculate

from ..common import named_series


def compute(*, high, low, close, talib):
    result = _calculate(high=high, low=low, close=close, talib=talib)
    return named_series(result, "ta.hlc3", "hlc3")
