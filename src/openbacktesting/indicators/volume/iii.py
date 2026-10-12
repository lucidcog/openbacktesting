"""ta.iii：独立公式与固定初始化契约。"""

from ..calculus import clean, ratio


def compute(*, high, low, close, volume):
    return ratio(
        clean(volume) * (2 * clean(close) - clean(high) - clean(low)), clean(high) - clean(low)
    ).rename("iii")
