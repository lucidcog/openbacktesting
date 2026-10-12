"""ta.rvol：独立公式与固定初始化契约。"""

from ..calculus import clean, ratio


def compute(*, volume, length):
    volume = clean(volume)
    return ratio(volume, volume.shift(1).rolling(length).mean()).rename("rvol")
