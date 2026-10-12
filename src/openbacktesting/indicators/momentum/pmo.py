"""ta.pmo: Independent formula with a fixed initialization contract."""

import pandas as pd

from ..calculus import average, clean, ratio


def compute(*, close, length, smooth, signal):
    close = clean(close)
    roc = 100 * (ratio(close, close.shift(1)) - 1)
    first = average(roc, length, alpha=2 / length)
    pmo = average(first * 10, smooth, alpha=2 / smooth)
    return pd.DataFrame({"pmo": pmo, "signal": average(pmo, signal)})
