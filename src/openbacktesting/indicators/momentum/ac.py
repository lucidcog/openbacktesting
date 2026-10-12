"""ta.ac: Independent formula with a fixed initialization contract."""

from ..calculus import clean


def compute(*, high, low, fast, slow, signal):
    middle = (clean(high) + clean(low)) / 2
    ao = middle.rolling(fast).mean() - middle.rolling(slow).mean()
    return (ao - ao.rolling(signal).mean()).rename("ac")
