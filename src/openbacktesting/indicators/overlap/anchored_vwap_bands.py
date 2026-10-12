"""条件 VWAP 的成交量加权总体标准差带。"""

from .anchored_vwap import _calculate


def compute(*, source, volume, anchor, stdev_mult):
    return _calculate(
        source=source,
        volume=volume,
        anchor=anchor,
        indicator="ta.anchored_vwap_bands",
        stdev_mult=stdev_mult,
    )
