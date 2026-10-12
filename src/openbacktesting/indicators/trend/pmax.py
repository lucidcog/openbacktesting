"""ta.pmax：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.trend.pmax import pmax as _calculate

from ..common import named_series


def compute(*, high, low, close, length, multiplier, mamode, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        length=length,
        multiplier=multiplier,
        mamode=mamode,
        talib=talib,
    )
    return named_series(result, "ta.pmax", "pmax")
