"""ta.crsi：独立公式与固定初始化契约。"""

import numpy as np
import pandas as pd

from ..calculus import clean, strength


def compute(*, close, length, streak, rank):
    close = clean(close)
    delta = close.diff()
    streaks = np.full(len(close), np.nan)
    previous = 0.0
    for i, value in enumerate(delta):
        if not np.isfinite(value):
            previous = 0.0
        elif value == 0:
            previous = 0.0
            streaks[i] = previous
        else:
            sign = np.sign(value)
            previous = previous + sign if previous * sign > 0 else sign
            streaks[i] = previous
    streak_series = pd.Series(streaks, index=close.index)
    roc = (close / close.shift(1) - 1).where(close.shift(1) > 0)
    percentile = (roc.rolling(rank + 1).rank(method="min") - 1) * 100 / rank
    result = (strength(delta, length) + strength(streak_series.diff(), streak) + percentile) / 3
    return result.rename("crsi")
