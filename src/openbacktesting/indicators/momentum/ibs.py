"""ta.ibs：独立公式与固定初始化契约。"""

from ..calculus import clean, ratio


def compute(*, high, low, close):
    return ratio(clean(close) - clean(low), clean(high) - clean(low)).rename("ibs")
