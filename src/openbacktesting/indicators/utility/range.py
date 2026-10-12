"""ta.range：固定因果序列契约。"""

from ..calculus import clean


def compute(*, source, length):
    window = clean(source).rolling(length)
    return (window.max() - window.min()).rename("range")
