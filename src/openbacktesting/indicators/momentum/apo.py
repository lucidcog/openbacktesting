"""ta.apo：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.apo import apo as _calculate

from ..common import named_series


def compute(*, close, fast, slow, mamode, talib):
    result = _calculate(close=close, fast=fast, slow=slow, mamode=mamode, talib=talib)
    return named_series(result, "ta.apo", "apo")
