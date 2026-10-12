"""ta.t3：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.t3 import t3 as _calculate

from ..common import named_series


def compute(*, close, length, a, talib):
    result = _calculate(close=close, length=length, a=a, talib=talib)
    return named_series(result, "ta.t3", "t3")
