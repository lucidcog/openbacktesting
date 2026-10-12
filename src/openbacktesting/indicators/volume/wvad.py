"""ta.wvad: Independent formula with a fixed initialization contract."""

from ..calculus import clean, ratio


def compute(*, open_, high, low, close, volume):
    return ratio(clean(volume) * (clean(close) - clean(open_)), clean(high) - clean(low)).rename(
        "wvad"
    )
