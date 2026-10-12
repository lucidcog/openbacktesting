"""ta.adr：独立公式与固定初始化契约。"""

from ..calculus import clean


def compute(*, high, low, length):
    return (clean(high) - clean(low)).rolling(length).mean().rename("adr")
