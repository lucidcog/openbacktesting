"""ta.wavetrend: Independent formula with a fixed initialization contract."""

import pandas as pd

from ..calculus import average as ema
from ..calculus import clean, ratio


def compute(*, high, low, close, length, average, signal):
    price = (clean(high) + clean(low) + clean(close)) / 3
    basis = ema(price, length, seeded=False)
    deviation = ema((price - basis).abs(), length, seeded=False)
    normalized = ratio(price - basis, 0.015 * deviation)
    wave = ema(normalized, average, seeded=False)
    return pd.DataFrame({"wave": wave, "signal": wave.rolling(signal).mean()})
