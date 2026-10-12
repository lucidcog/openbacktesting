"""ta.rising：固定因果序列契约。"""

from ..calculus import clean


def compute(*, source, length):
    source = clean(source)
    previous = source.shift(1).rolling(length).max()
    result = (source > previous).astype(float)
    return result.where(source.notna() & previous.notna()).rename("rising")
