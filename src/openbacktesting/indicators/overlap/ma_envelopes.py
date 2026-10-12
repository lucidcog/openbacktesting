"""ta.ma_envelopes: Independent formula with a fixed initialization contract."""

import pandas as pd

from ..calculus import average, clean


def compute(*, close, length, percent, mamode):
    middle = clean(close).rolling(length).mean() if mamode == "sma" else average(close, length)
    return pd.DataFrame(
        {
            "middle": middle,
            "upper": middle * (1 + percent / 100),
            "lower": middle * (1 - percent / 100),
        }
    )
