"""ta.linreg：固定依赖的计算封装与规范输出。"""

import numpy as np
from pandas_ta_classic.overlap.linreg import linreg as _calculate

from ..common import named_series


def compute(*, close, length, talib, offset):
    result = _calculate(close=close, length=length, talib=talib)
    if offset and result is not None:
        slope = _calculate(close=close, length=length, talib=talib, slope=True)
        with np.errstate(over="ignore", invalid="ignore"):
            result = result - slope * float(offset)
    return named_series(result, "ta.linreg", "linreg")
