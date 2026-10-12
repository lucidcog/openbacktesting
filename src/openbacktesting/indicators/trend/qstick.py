"""ta.qstick：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.trend.qstick import qstick as _calculate

from ..common import named_series


def compute(*, open_, close, length, talib):
    result = _calculate(open_=open_, close=close, length=length, talib=talib)
    return named_series(result, "ta.qstick", "qstick")
