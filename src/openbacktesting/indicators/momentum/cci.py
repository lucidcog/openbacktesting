"""ta.cci：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.cci import cci as _calculate

from ..common import named_series


def compute(*, high, low, close, length, c, talib):
    result = _calculate(high=high, low=low, close=close, length=length, c=c, talib=talib)
    return named_series(result, "ta.cci", "cci")
