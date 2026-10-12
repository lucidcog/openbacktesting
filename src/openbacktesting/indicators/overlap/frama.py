"""ta.frama: Independent formula with a fixed initialization contract."""

import numpy as np
import pandas as pd

from ..calculus import clean


def compute(*, high, low, close, length):
    high, low, close = clean(high), clean(low), clean(close)
    half = length // 2
    small = (high.rolling(half).max() - low.rolling(half).min()) / half
    full = (high.rolling(length).max() - low.rolling(length).min()) / length
    combined = small + small.shift(half)
    with np.errstate(divide="ignore", invalid="ignore"):
        dimension = np.log(combined / full) / np.log(2)
        alpha = np.exp(-4.6 * (dimension - 1)).clip(0.01, 1)
    alpha = alpha.mask((combined == 0) & (full == 0), 1.0)
    result = np.full(len(close), np.nan)
    previous = np.nan
    for i, (price, weight) in enumerate(zip(close, alpha)):
        if not np.isfinite(price) or not np.isfinite(weight):
            previous = np.nan
        else:
            previous = (
                price if not np.isfinite(previous) else weight * price + (1 - weight) * previous
            )
            result[i] = previous
    return pd.Series(result, index=close.index, name="frama")
