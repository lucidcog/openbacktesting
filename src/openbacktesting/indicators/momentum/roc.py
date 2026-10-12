"""ta.roc：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.roc import roc as _calculate

from ..common import named_series


def compute(*, close, length, scalar, talib):
    result = _calculate(close=close, length=length, scalar=scalar, talib=talib)
    return named_series(result, "ta.roc", "roc")
