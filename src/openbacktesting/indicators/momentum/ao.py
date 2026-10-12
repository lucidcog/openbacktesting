"""ta.ao：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.ao import ao as _calculate

from ..common import named_series


def compute(*, high, low, fast, slow, talib):
    result = _calculate(high=high, low=low, fast=fast, slow=slow, talib=talib)
    return named_series(result, "ta.ao", "ao")
