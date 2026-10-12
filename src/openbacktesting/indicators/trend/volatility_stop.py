"""ta.volatility_stop：独立公式与固定初始化契约。"""

import numpy as np
import pandas as pd

from ..calculus import atr, segments


def compute(*, high, low, close, length, multiplier):
    width = atr(high, low, close, length).to_numpy() * multiplier
    prices = close.to_numpy()
    stop = np.full(len(close), np.nan)
    direction = stop.copy()
    valid = np.isfinite(np.column_stack([high, low, close])).all(axis=1)
    for start, end in segments(valid):
        if end - start <= length:
            continue
        bullish = prices[start + length - 1] > prices[start]
        initial = prices[start : start + length]
        extreme = initial.max() if bullish else initial.min()
        confirmed = False
        for i in range(start + length, end):
            level = extreme - width[i - 1] if bullish else extreme + width[i - 1]
            if confirmed:
                stop[i], direction[i] = level, 1 if bullish else -1
            reverse = prices[i] < level if bullish else prices[i] > level
            if reverse:
                bullish = not bullish
                extreme = prices[i]
                confirmed = True
            else:
                extreme = max(extreme, prices[i]) if bullish else min(extreme, prices[i])
    return pd.DataFrame({"stop": stop, "direction": direction}, index=close.index)
