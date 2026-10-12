"""ta.aroon：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.trend.aroon import aroon as _calculate

from ..common import named_frame


def compute(*, high, low, length, scalar, talib):
    result = _calculate(high=high, low=low, length=length, scalar=scalar, talib=talib)
    return named_frame(
        result,
        "ta.aroon",
        {
            f"AROOND_{length}": "down",
            f"AROONU_{length}": "up",
            f"AROONOSC_{length}": "oscillator",
        },
    )
