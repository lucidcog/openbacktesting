"""ta.bbands：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volatility.bbands import bbands as _calculate

from ..common import named_frame


def compute(*, close, length, std, ddof, mamode, talib):
    result = _calculate(close=close, length=length, std=std, ddof=ddof, mamode=mamode, talib=talib)
    return named_frame(
        result,
        "ta.bbands",
        {
            f"BBL_{length}_{std}": "lower",
            f"BBM_{length}_{std}": "middle",
            f"BBU_{length}_{std}": "upper",
            f"BBB_{length}_{std}": "bandwidth",
            f"BBP_{length}_{std}": "percent",
        },
    )
