"""ta.ibs: Independent formula with a fixed initialization contract."""

from ..calculus import clean, ratio


def compute(*, high, low, close):
    return ratio(clean(close) - clean(low), clean(high) - clean(low)).rename("ibs")
