"""ta.zlma：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.zlma import zlma as _calculate

from ..common import named_series


def compute(*, close, length, mamode, talib):
    result = _calculate(close=close, length=length, mamode=mamode, talib=talib)
    return named_series(result, "ta.zlma", "zlma")
