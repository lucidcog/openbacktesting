"""ta.log_return：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.performance.log_return import log_return as _calculate

from ..common import named_series


def compute(*, close, length, cumulative, talib):
    result = _calculate(close=close, length=length, cumulative=cumulative, talib=talib)
    return named_series(result, "ta.log_return", "log_return")
