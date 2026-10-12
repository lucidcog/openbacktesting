"""ta.adosc：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volume.adosc import adosc as _calculate

from ..common import named_series


def compute(*, high, low, close, volume, fast, slow, open_, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        volume=volume,
        fast=fast,
        slow=slow,
        open_=open_,
        talib=talib,
    )
    return named_series(result, "ta.adosc", "adosc")
