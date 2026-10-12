"""ta.midprice：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.midprice import midprice as _calculate

from ..common import named_series


def compute(*, high, low, length, talib):
    result = _calculate(high=high, low=low, length=length, talib=talib)
    return named_series(result, "ta.midprice", "midprice")
