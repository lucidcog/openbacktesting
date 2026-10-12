"""ta.mcgd：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.mcgd import mcgd as _calculate

from ..common import named_series


def compute(*, close, length, c, talib):
    result = _calculate(close=close, length=length, c=c, talib=talib)
    return named_series(result, "ta.mcgd", "mcgd")
