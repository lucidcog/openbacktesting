"""ta.entropy：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.statistics.entropy import entropy as _calculate

from ..common import named_series


def compute(*, close, length, base, talib):
    result = _calculate(close=close, length=length, base=base, talib=talib)
    return named_series(result, "ta.entropy", "entropy")
