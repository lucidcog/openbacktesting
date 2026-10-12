"""Volume-weighted population standard-deviation bands for conditional VWAP."""

from .anchored_vwap import _calculate


def compute(*, source, volume, anchor, stdev_mult):
    return _calculate(
        source=source,
        volume=volume,
        anchor=anchor,
        indicator="ta.anchored_vwap_bands",
        stdev_mult=stdev_mult,
    )
