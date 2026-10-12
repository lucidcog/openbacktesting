"""ta.psl：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.psl import psl as _calculate

from ..common import named_series


def compute(*, close, length, scalar, drift, open_, talib):
    result = _calculate(
        close=close, length=length, scalar=scalar, drift=drift, open_=open_, talib=talib
    )
    return named_series(result, "ta.psl", "psl")
