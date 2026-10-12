"""ta.pvol：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volume.pvol import pvol as _calculate

from ..common import named_series


def compute(*, close, volume, talib):
    result = _calculate(close=close, volume=volume, talib=talib)
    return named_series(result, "ta.pvol", "pvol")
