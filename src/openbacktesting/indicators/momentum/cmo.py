"""ta.cmo：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.cmo import cmo as _calculate

from ..common import named_series


def compute(*, close, length, scalar, drift, talib):
    result = _calculate(close=close, length=length, scalar=scalar, drift=drift, talib=talib)
    return named_series(result, "ta.cmo", "cmo")
