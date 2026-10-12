"""ta.ma：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.ma import ma as _calculate

from ..common import named_series


def compute(*, source, name, length, talib):
    result = _calculate(source=source, name=name, length=length, talib=talib)
    return named_series(result, "ta.ma", "ma")
