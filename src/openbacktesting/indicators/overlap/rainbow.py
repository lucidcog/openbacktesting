"""ta.rainbow：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.rainbow import rainbow as _calculate

from ..common import named_frame


def compute(*, close, length, talib):
    result = _calculate(close=close, length=length, talib=talib)
    return named_frame(
        result,
        "ta.rainbow",
        {
            "RAINBOW_1": "ma1",
            "RAINBOW_2": "ma2",
            "RAINBOW_3": "ma3",
            "RAINBOW_4": "ma4",
            "RAINBOW_5": "ma5",
            "RAINBOW_6": "ma6",
            "RAINBOW_7": "ma7",
            "RAINBOW_8": "ma8",
            "RAINBOW_9": "ma9",
            "RAINBOW_10": "ma10",
        },
    )
