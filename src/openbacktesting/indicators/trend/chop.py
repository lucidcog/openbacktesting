"""ta.chop：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.trend.chop import chop as _calculate

from ..common import named_series


def compute(*, high, low, close, length, atr_length, ln, scalar, drift, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        length=length,
        atr_length=atr_length,
        ln=ln,
        scalar=scalar,
        drift=drift,
        talib=talib,
    )
    return named_series(result, "ta.chop", "chop")
