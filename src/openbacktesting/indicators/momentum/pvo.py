"""ta.pvo: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.pvo import pvo as _calculate

from ..common import named_frame


def compute(*, volume, fast, slow, signal, scalar, talib):
    result = _calculate(
        volume=volume, fast=fast, slow=slow, signal=signal, scalar=scalar, talib=talib
    )
    return named_frame(
        result,
        "ta.pvo",
        {
            f"PVO_{fast}_{slow}_{signal}": "pvo",
            f"PVOh_{fast}_{slow}_{signal}": "histogram",
            f"PVOs_{fast}_{slow}_{signal}": "signal",
        },
    )
