"""ta.supertrend: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.supertrend import supertrend as _calculate

from ..common import named_frame


def compute(*, high, low, close, length, multiplier, talib):
    result = _calculate(
        high=high, low=low, close=close, length=length, multiplier=multiplier, talib=talib
    )
    return named_frame(
        result,
        "ta.supertrend",
        {
            f"SUPERT_{length}_{multiplier}": "trend",
            f"SUPERTd_{length}_{multiplier}": "direction",
            f"SUPERTl_{length}_{multiplier}": "long",
            f"SUPERTs_{length}_{multiplier}": "short",
        },
    )
