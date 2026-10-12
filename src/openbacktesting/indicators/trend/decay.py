"""ta.decay：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.trend.decay import decay as _calculate

from ..common import named_series


def compute(*, close, length, mode, kind, talib):
    result = _calculate(close=close, length=length, mode=mode, kind=kind, talib=talib)
    return named_series(result, "ta.decay", "decay")
