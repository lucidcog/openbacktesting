"""ta.long_run：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.trend.long_run import long_run as _calculate

from ..common import named_series


def compute(*, fast, slow, length, talib):
    result = _calculate(fast=fast, slow=slow, length=length, talib=talib)
    return named_series(result, "ta.long_run", "long_run")
