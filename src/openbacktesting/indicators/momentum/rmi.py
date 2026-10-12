"""ta.rmi: Independent formula with a fixed initialization contract."""

from ..calculus import clean, strength


def compute(*, close, length, momentum):
    return strength(clean(close).diff(momentum), length).rename("rmi")
