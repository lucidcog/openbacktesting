"""ta.quantile：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.statistics.quantile import quantile as _calculate

from ..common import named_series


def compute(*, close, length, q, talib):
    result = _calculate(close=close, length=length, q=q, talib=talib)
    return named_series(result, "ta.quantile", "quantile")
