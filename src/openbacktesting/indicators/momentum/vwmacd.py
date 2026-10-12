"""ta.vwmacd: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.vwmacd import vwmacd as _calculate

from ..common import named_frame


def compute(*, close, volume, fast, slow, signal, talib):
    result = _calculate(
        close=close, volume=volume, fast=fast, slow=slow, signal=signal, talib=talib
    )
    return named_frame(
        result,
        "ta.vwmacd",
        {
            f"VWMACD_{fast}_{slow}_{signal}": "macd",
            f"VWMACDh_{fast}_{slow}_{signal}": "histogram",
            f"VWMACDs_{fast}_{slow}_{signal}": "signal",
        },
    )
