"""ta.kst: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.kst import kst as _calculate

from ..common import named_frame


def compute(*, close, roc1, roc2, roc3, roc4, sma1, sma2, sma3, sma4, signal, drift, talib):
    result = _calculate(
        close=close,
        roc1=roc1,
        roc2=roc2,
        roc3=roc3,
        roc4=roc4,
        sma1=sma1,
        sma2=sma2,
        sma3=sma3,
        sma4=sma4,
        signal=signal,
        drift=drift,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.kst",
        {
            f"KST_{roc1}_{roc2}_{roc3}_{roc4}_{sma1}_{sma2}_{sma3}_{sma4}": "kst",
            f"KSTs_{signal}": "signal",
        },
    )
