"""ta.iii: Independent formula with a fixed initialization contract."""

from ..calculus import clean, ratio


def compute(*, high, low, close, volume):
    return ratio(
        clean(volume) * (2 * clean(close) - clean(high) - clean(low)), clean(high) - clean(low)
    ).rename("iii")
