"""ta.kvo: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.kvo import kvo as _calculate

from ..common import named_frame


def compute(*, high, low, close, volume, fast, slow, signal, mamode, drift, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        volume=volume,
        fast=fast,
        slow=slow,
        signal=signal,
        mamode=mamode,
        drift=drift,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.kvo",
        {
            f"KVO_{fast}_{slow}_{signal}": "kvo",
            f"KVOs_{fast}_{slow}_{signal}": "signal",
        },
    )
