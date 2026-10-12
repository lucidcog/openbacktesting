"""Doji: Threshold based on mean historical range; explicit local implementation avoids implicit TA-Lib and full-sample epsilon."""

import numpy as np

from ..calculus import clean


def compute(*, open_, high, low, close, length, factor):
    width = clean(high) - clean(low)
    body = (clean(close) - clean(open_)).abs()
    threshold = width.rolling(length).mean().shift(1) * factor / 100
    history = np.isfinite(np.column_stack([open_, high, low, close])).all(axis=1)
    valid = body.notna() & threshold.notna()
    valid &= clean(close).where(history).rolling(length + 1).count() == length + 1
    result = ((body <= threshold).astype(np.int16) * 100).rename("cdl_doji")
    result.attrs["indicator_valid"] = valid.to_numpy()
    return result
