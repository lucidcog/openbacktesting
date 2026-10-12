"""ta.amat: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.amat import amat as _calculate

from ..common import named_frame


def compute(*, close, fast, slow, lookback, mamode, talib):
    result = _calculate(
        close=close, fast=fast, slow=slow, lookback=lookback, mamode=mamode, talib=talib
    )
    return named_frame(
        result,
        "ta.amat",
        {
            f"AMAT{mamode[0]}_LR_{fast}_{slow}_{lookback}": "long",
            f"AMAT{mamode[0]}_SR_{fast}_{slow}_{lookback}": "short",
        },
    )
