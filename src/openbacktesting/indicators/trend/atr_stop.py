"""ta.atr_stop: Independent formula with a fixed initialization contract."""

import numpy as np
import pandas as pd

from ..calculus import atr, clean


def compute(*, high, low, close, length, multiplier, end_type):
    high, low, close = clean(high), clean(low), clean(close)
    width = atr(high, low, close, length).to_numpy() * multiplier
    prices, highs, lows = close.to_numpy(), high.to_numpy(), low.to_numpy()
    stop = np.full(len(close), np.nan)
    direction = stop.copy()
    upper = lower = np.nan
    bullish = True
    for i in range(1, len(close)):
        if not np.isfinite(width[i]) or not np.isfinite(prices[i]):
            upper = lower = np.nan
            continue
        hi = (prices[i] if end_type == "close" else highs[i]) + width[i]
        lo = (prices[i] if end_type == "close" else lows[i]) - width[i]
        if not np.isfinite(upper):
            bullish = prices[i] >= prices[i - 1]
            upper, lower = hi, lo
        if hi < upper or prices[i - 1] > upper:
            upper = hi
        if lo > lower or prices[i - 1] < lower:
            lower = lo
        bullish = prices[i] > (lower if bullish else upper)
        stop[i] = lower if bullish else upper
        direction[i] = 1 if bullish else -1
    return pd.DataFrame({"stop": stop, "direction": direction}, index=close.index)
