"""ta.coppock：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.coppock import coppock as _calculate

from ..common import named_series


def compute(*, close, length, fast, slow, talib):
    result = _calculate(close=close, length=length, fast=fast, slow=slow, talib=talib)
    return named_series(result, "ta.coppock", "coppock")
