"""ta.kdj：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.kdj import kdj as _calculate

from ..common import named_frame


def compute(*, high, low, close, length, signal, talib):
    result = _calculate(high=high, low=low, close=close, length=length, signal=signal, talib=talib)
    return named_frame(
        result,
        "ta.kdj",
        {
            f"K_{length}_{signal}": "k",
            f"D_{length}_{signal}": "d",
            f"J_{length}_{signal}": "j",
        },
    )
