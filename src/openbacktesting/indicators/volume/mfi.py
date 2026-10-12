"""ta.mfi：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volume.mfi import mfi as _calculate

from ..common import named_series


def compute(*, high, low, close, volume, length, drift, talib):
    result = _calculate(
        high=high, low=low, close=close, volume=volume, length=length, drift=drift, talib=talib
    )
    return named_series(result, "ta.mfi", "mfi")
