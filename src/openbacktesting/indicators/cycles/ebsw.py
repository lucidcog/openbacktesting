"""ta.ebsw：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.cycles.ebsw import ebsw as _calculate

from ..common import named_series


def compute(*, close, length, bars, talib):
    result = _calculate(close=close, length=length, bars=bars, talib=talib)
    return named_series(result, "ta.ebsw", "ebsw")
