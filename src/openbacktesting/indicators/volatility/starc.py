"""ta.starc：独立公式与固定初始化契约。"""

import pandas as pd

from ..calculus import atr, clean


def compute(*, high, low, close, length, atr_length, multiplier):
    middle = clean(close).rolling(length).mean()
    spread = atr(high, low, close, atr_length) * multiplier
    return pd.DataFrame({"middle": middle, "upper": middle + spread, "lower": middle - spread})
