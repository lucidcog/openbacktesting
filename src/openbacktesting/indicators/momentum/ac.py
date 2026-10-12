"""ta.ac：独立公式与固定初始化契约。"""

from ..calculus import clean


def compute(*, high, low, fast, slow, signal):
    middle = (clean(high) + clean(low)) / 2
    ao = middle.rolling(fast).mean() - middle.rolling(slow).mean()
    return (ao - ao.rolling(signal).mean()).rename("ac")
