"""ta.pvt：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volume.pvt import pvt as _calculate

from ..common import named_series


def compute(*, close, volume, drift, talib):
    result = _calculate(close=close, volume=volume, drift=drift, talib=talib)
    return named_series(result, "ta.pvt", "pvt")
