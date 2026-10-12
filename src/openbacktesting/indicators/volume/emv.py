"""ta.emv：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volume.emv import emv as _calculate

from ..common import named_series


def compute(*, high, low, volume, drift, talib):
    result = _calculate(high=high, low=low, volume=volume, drift=drift, talib=talib)
    return named_series(result, "ta.emv", "emv")
