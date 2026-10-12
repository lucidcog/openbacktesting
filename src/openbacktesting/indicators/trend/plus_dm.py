"""ta.plus_dm：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.trend.plus_dm import plus_dm as _calculate

from ..common import named_series


def compute(*, high, low, length, drift, talib):
    result = _calculate(high=high, low=low, length=length, drift=drift, talib=talib)
    return named_series(result, "ta.plus_dm", "plus_dm")
