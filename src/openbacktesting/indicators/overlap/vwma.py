"""ta.vwma：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.vwma import vwma as _calculate

from ..common import named_series


def compute(*, close, volume, length, talib):
    result = _calculate(close=close, volume=volume, length=length, talib=talib)
    return named_series(result, "ta.vwma", "vwma")
