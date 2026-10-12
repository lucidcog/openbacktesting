"""ta.aobv: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.aobv import aobv as _calculate

from ..common import named_frame


def compute(*, close, volume, fast, slow, max_lookback, min_lookback, mamode, talib):
    result = _calculate(
        close=close,
        volume=volume,
        fast=fast,
        slow=slow,
        max_lookback=max_lookback,
        min_lookback=min_lookback,
        mamode=mamode,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.aobv",
        {
            "OBV": "obv",
            f"OBV_min_{min_lookback}": "minimum",
            f"OBV_max_{max_lookback}": "maximum",
            f"OBV{mamode[0]}_{fast}": "fast",
            f"OBV{mamode[0]}_{slow}": "slow",
            "AOBV_LR_2": "long",
            "AOBV_SR_2": "short",
        },
    )
