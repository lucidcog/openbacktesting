"""ta.smi_stochastic: Independent formula with a fixed initialization contract."""

import pandas as pd

from ..calculus import average, clean, ratio


def compute(*, high, low, close, length, smooth, double, signal):
    hi, lo = clean(high).rolling(length).max(), clean(low).rolling(length).min()
    distance = clean(close) - (hi + lo) / 2
    spread = hi - lo
    numerator = average(average(distance, smooth, seeded=False), double, seeded=False)
    denominator = average(average(spread, smooth, seeded=False), double, seeded=False)
    smi = ratio(200 * numerator, denominator)
    return pd.DataFrame({"smi": smi, "signal": average(smi, signal, seeded=False)})
