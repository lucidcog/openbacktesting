"""ta.macdext: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.macdext import macdext as _calculate

from ..common import named_frame


def compute(*, close, fast, slow, signal, fastmatype, slowmatype, signalmatype, talib):
    result = _calculate(
        close=close,
        fast=fast,
        slow=slow,
        signal=signal,
        fastmatype=fastmatype,
        slowmatype=slowmatype,
        signalmatype=signalmatype,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.macdext",
        {
            f"MACDEXT_{fast}_{slow}_{signal}": "macd",
            f"MACDEXTs_{fast}_{slow}_{signal}": "signal",
            f"MACDEXTh_{fast}_{slow}_{signal}": "histogram",
        },
    )
