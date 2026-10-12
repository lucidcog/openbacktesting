"""ta.macd：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.macd import macd as _calculate

from ..common import named_frame


def compute(*, close, fast, slow, signal, offset, asmode, signal_indicators, talib):
    result = _calculate(
        close=close,
        fast=fast,
        slow=slow,
        signal=signal,
        offset=offset,
        asmode=asmode,
        signal_indicators=signal_indicators,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.macd",
        {
            f"MACD_{fast}_{slow}_{signal}": "macd",
            f"MACDh_{fast}_{slow}_{signal}": "histogram",
            f"MACDs_{fast}_{slow}_{signal}": "signal",
        },
    )
