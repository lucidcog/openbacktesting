"""ta.falling：固定因果序列契约。"""

from ..calculus import clean


def compute(*, source, length):
    source = clean(source)
    previous = source.shift(1).rolling(length).min()
    result = (source < previous).astype(float)
    return result.where(source.notna() & previous.notna()).rename("falling")
