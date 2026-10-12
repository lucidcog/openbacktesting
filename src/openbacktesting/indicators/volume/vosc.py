"""ta.vosc：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volume.vosc import vosc as _calculate

from ..common import named_series


def compute(*, volume, fast, slow, talib):
    result = _calculate(volume=volume, fast=fast, slow=slow, talib=talib)
    return named_series(result, "ta.vosc", "vosc")
