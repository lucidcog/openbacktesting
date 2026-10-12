"""ta.accbands：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volatility.accbands import accbands as _calculate

from ..common import named_frame


def compute(*, high, low, close, length, c, mamode, drift, talib):
    result = _calculate(
        high=high, low=low, close=close, length=length, c=c, mamode=mamode, drift=drift, talib=talib
    )
    return named_frame(
        result,
        "ta.accbands",
        {
            f"ACCBL_{length}": "lower",
            f"ACCBM_{length}": "middle",
            f"ACCBU_{length}": "upper",
        },
    )
