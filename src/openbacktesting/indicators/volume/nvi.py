"""NVI: Update the preceding index by the price ratio under the volume condition."""

import numpy as np
import pandas as pd


def compute(*, close, volume, length, initial):
    prices, amounts = close.to_numpy(), volume.to_numpy()
    result = np.full(len(close), np.nan)
    value = None
    for i in range(len(close)):
        if not np.isfinite(prices[i]) or not np.isfinite(amounts[i]):
            continue
        if value is None:
            value = float(initial)
        elif (
            i < length
            or not np.isfinite(prices[i - length])
            or prices[i - length] == 0
            or not np.isfinite(amounts[i - 1])
        ):
            continue
        elif amounts[i] < amounts[i - 1]:
            value *= prices[i] / prices[i - length]
        result[i] = value
    return pd.Series(result, index=close.index, name="nvi")
