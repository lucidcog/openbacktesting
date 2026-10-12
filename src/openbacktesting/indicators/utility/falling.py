"""ta.falling: Fixed causal sequence contract."""

from ..calculus import clean


def compute(*, source, length):
    source = clean(source)
    previous = source.shift(1).rolling(length).min()
    result = (source < previous).astype(float)
    return result.where(source.notna() & previous.notna()).rename("falling")
