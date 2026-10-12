"""ta.macdfix: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.macdfix import macdfix as _calculate

from ..common import named_frame


def compute(*, close, signal, talib):
    result = _calculate(close=close, signal=signal, talib=talib)
    return named_frame(
        result,
        "ta.macdfix",
        {
            f"MACDFIX_{signal}_{signal}": "macd",
            f"MACDFIXh_{signal}_{signal}": "histogram",
            f"MACDFIXs_{signal}_{signal}": "signal",
        },
    )
