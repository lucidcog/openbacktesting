"""ta.hilo: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.hilo import hilo as _calculate

from ..common import named_frame


def compute(*, high, low, close, high_length, low_length, mamode, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        high_length=high_length,
        low_length=low_length,
        mamode=mamode,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.hilo",
        {
            f"HILO_{high_length}_{low_length}": "hilo",
            f"HILOl_{high_length}_{low_length}": "long",
            f"HILOs_{high_length}_{low_length}": "short",
        },
    )
