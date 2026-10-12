"""ta.vwap：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.vwap import vwap as _calculate

from ..common import named_series


def compute(*, high, low, close, volume, anchor, talib):
    result = _calculate(high=high, low=low, close=close, volume=volume, anchor=anchor, talib=talib)
    return named_series(result, "ta.vwap", "vwap")
