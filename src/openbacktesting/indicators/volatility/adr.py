"""ta.adr: Independent formula with a fixed initialization contract."""

from ..calculus import clean


def compute(*, high, low, length):
    return (clean(high) - clean(low)).rolling(length).mean().rename("adr")
