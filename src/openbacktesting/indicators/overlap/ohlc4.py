"""ta.ohlc4：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.ohlc4 import ohlc4 as _calculate

from ..common import named_series


def compute(*, open_, high, low, close, talib):
    result = _calculate(open_=open_, high=high, low=low, close=close, talib=talib)
    return named_series(result, "ta.ohlc4", "ohlc4")
