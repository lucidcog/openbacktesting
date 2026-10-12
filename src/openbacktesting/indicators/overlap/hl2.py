"""ta.hl2：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.hl2 import hl2 as _calculate

from ..common import named_series


def compute(*, high, low, talib):
    result = _calculate(high=high, low=low, talib=talib)
    return named_series(result, "ta.hl2", "hl2")
