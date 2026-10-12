"""ta.stdev：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.statistics.stdev import stdev as _calculate

from ..common import named_series


def compute(*, close, length, ddof, talib):
    result = _calculate(close=close, length=length, ddof=ddof, talib=talib)
    return named_series(result, "ta.stdev", "stdev")
