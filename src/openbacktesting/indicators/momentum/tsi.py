"""ta.tsi: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.tsi import tsi as _calculate

from ..common import named_frame


def compute(*, close, fast, slow, signal, scalar, mamode, drift, talib):
    result = _calculate(
        close=close,
        fast=fast,
        slow=slow,
        signal=signal,
        scalar=scalar,
        mamode=mamode,
        drift=drift,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.tsi",
        {
            f"TSI_{fast}_{slow}_{signal}": "tsi",
            f"TSIs_{fast}_{slow}_{signal}": "signal",
        },
    )
