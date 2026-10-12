"""ta.hwma：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.hwma import hwma as _calculate

from ..common import named_series


def compute(*, close, na, nb, nc, talib):
    result = _calculate(close=close, na=na, nb=nb, nc=nc, talib=talib)
    return named_series(result, "ta.hwma", "hwma")
