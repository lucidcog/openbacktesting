"""ta.ema：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.ema import ema as _calculate

from ..common import named_series


def compute(*, close, length, adjust, sma, offset, talib):
    result = _calculate(
        close=close, length=length, adjust=adjust, sma=sma, offset=offset, talib=talib
    )
    return named_series(result, "ta.ema", "ema")
