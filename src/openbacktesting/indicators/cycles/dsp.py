"""ta.dsp：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.cycles.dsp import dsp as _calculate

from ..common import named_series


def compute(*, close, length, talib):
    result = _calculate(close=close, length=length, talib=talib)
    return named_series(result, "ta.dsp", "dsp")
