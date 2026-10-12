"""ta.jma：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.jma import jma as _calculate

from ..common import named_series


def compute(*, close, length, phase, talib):
    result = _calculate(close=close, length=length, phase=phase, talib=talib)
    return named_series(result, "ta.jma", "jma")
