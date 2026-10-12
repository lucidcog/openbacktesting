"""ta.dm：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.dm import dm as _calculate

from ..common import named_frame


def compute(*, high, low, length, mamode, drift, talib):
    result = _calculate(high=high, low=low, length=length, mamode=mamode, drift=drift, talib=talib)
    return named_frame(
        result,
        "ta.dm",
        {
            f"DMP_{length}": "positive",
            f"DMN_{length}": "negative",
        },
    )
