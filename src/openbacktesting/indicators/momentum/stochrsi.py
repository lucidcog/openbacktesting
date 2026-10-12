"""ta.stochrsi：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.stochrsi import stochrsi as _calculate

from ..common import named_frame


def compute(*, close, length, rsi_length, k, d, mamode, talib):
    result = _calculate(
        close=close, length=length, rsi_length=rsi_length, k=k, d=d, mamode=mamode, talib=talib
    )
    return named_frame(
        result,
        "ta.stochrsi",
        {
            f"STOCHRSIk_{length}_{rsi_length}_{k}_{d}": "k",
            f"STOCHRSId_{length}_{rsi_length}_{k}_{d}": "d",
        },
    )
