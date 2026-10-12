"""ta.pivothigh: Fixed causal sequence contract."""

import numpy as np
import pandas as pd

from ..calculus import clean


def compute(*, high, left, right):
    source = clean(high)
    candidate = source.shift(right)
    lhs = source.shift(right + 1).rolling(left).max()
    rhs = source.rolling(right).max()
    event = (candidate >= lhs) & (candidate > rhs)
    positions = pd.Series(np.arange(len(source), dtype=float), index=source.index)
    return pd.DataFrame(
        {
            "value": candidate.where(event),
            "pivot_bar": (positions - right).where(event),
            "confirmed_at": positions.where(event),
        },
        index=source.index,
    )
