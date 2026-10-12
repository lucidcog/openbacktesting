"""ta.rvol: Independent formula with a fixed initialization contract."""

from ..calculus import clean, ratio


def compute(*, volume, length):
    volume = clean(volume)
    return ratio(volume, volume.shift(1).rolling(length).mean()).rename("rvol")
