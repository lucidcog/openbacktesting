"""ta.percent_return：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.performance.percent_return import percent_return as _calculate

from ..common import named_series


def compute(*, close, length, cumulative, talib):
    result = _calculate(close=close, length=length, cumulative=cumulative, talib=talib)
    return named_series(result, "ta.percent_return", "percent_return")
