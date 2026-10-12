"""ta.alma: Computation wrapper for the pinned dependency with canonical outputs."""

import numpy as np
import pandas as pd
from pandas_ta_classic.overlap.alma import alma as _calculate

from ..common import named_series


def compute(*, close, length, sigma, distribution_offset, talib, floor):
    if floor:
        center = np.floor(distribution_offset * (length - 1))
        distance = np.arange(length, dtype=float) - center
        # The center is an integer, ensuring at least one weight is exactly 1; other weights can safely underflow for extreme sigma.
        with np.errstate(over="ignore", under="ignore"):
            scaled = distance * (sigma / length)
            weights = np.exp(-0.5 * scaled * scaled)
        weights /= weights.sum()
        output = np.full(len(close), np.nan)
        if len(close) >= length:
            windows = np.lib.stride_tricks.sliding_window_view(close.to_numpy(), length)
            with np.errstate(invalid="ignore", over="ignore"):
                values = windows @ weights[::-1]
            output[length - 1 :] = np.where(np.isfinite(windows).all(axis=1), values, np.nan)
        return pd.Series(output, index=close.index, name="alma")
    result = _calculate(
        close=close,
        length=length,
        sigma=sigma,
        distribution_offset=distribution_offset,
        talib=talib,
    )
    return named_series(result, "ta.alma", "alma")
