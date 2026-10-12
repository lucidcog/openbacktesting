"""ta.cg：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.cg import cg as _calculate

from ..common import named_series


def compute(*, close, length, talib):
    result = _calculate(close=close, length=length, talib=talib)
    return named_series(result, "ta.cg", "cg")
