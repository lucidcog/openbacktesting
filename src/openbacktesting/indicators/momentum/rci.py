"""ta.rci: Independent formula with a fixed initialization contract."""

import numpy as np

from ..calculus import clean


def compute(*, close, length):
    time = np.arange(length, dtype=float)
    time -= time.mean()
    time_norm = np.dot(time, time)

    def correlation(values):
        _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
        ranks = (np.cumsum(counts) - (counts - 1) / 2)[inverse]
        ranks -= ranks.mean()
        norm = np.dot(ranks, ranks)
        return 100 * np.dot(time, ranks) / np.sqrt(time_norm * norm) if norm else np.nan

    return clean(close).rolling(length).apply(correlation, raw=True).rename("rci")
