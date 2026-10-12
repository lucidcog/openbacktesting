"""ta.stoch: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.stoch import stoch as _calculate

from ..common import named_frame


def compute(*, high, low, close, k, d, smooth_k, mamode, talib):
    result = _calculate(
        high=high, low=low, close=close, k=k, d=d, smooth_k=smooth_k, mamode=mamode, talib=talib
    )
    return named_frame(
        result,
        "ta.stoch",
        {
            f"STOCHk_{k}_{d}_{smooth_k}": "k",
            f"STOCHd_{k}_{d}_{smooth_k}": "d",
        },
    )
