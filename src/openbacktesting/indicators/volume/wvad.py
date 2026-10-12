"""ta.wvad：独立公式与固定初始化契约。"""

from ..calculus import clean, ratio


def compute(*, open_, high, low, close, volume):
    return ratio(clean(volume) * (clean(close) - clean(open_)), clean(high) - clean(low)).rename(
        "wvad"
    )
