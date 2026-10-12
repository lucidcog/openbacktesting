"""ta.stochf：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.stochf import stochf as _calculate

from ..common import named_frame


def compute(*, high, low, close, fastk, fastd, mamode, talib):
    result = _calculate(
        high=high, low=low, close=close, fastk=fastk, fastd=fastd, mamode=mamode, talib=talib
    )
    return named_frame(
        result,
        "ta.stochf",
        {
            f"STOCHFk_{fastk}_{fastd}": "k",
            f"STOCHFd_{fastk}_{fastd}": "d",
        },
    )
