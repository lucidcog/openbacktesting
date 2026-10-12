"""ta.lrsi：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.lrsi import lrsi as _calculate

from ..common import named_series


def compute(*, close, length, gamma, talib):
    result = _calculate(close=close, length=length, gamma=gamma, talib=talib)
    return named_series(result, "ta.lrsi", "lrsi")
