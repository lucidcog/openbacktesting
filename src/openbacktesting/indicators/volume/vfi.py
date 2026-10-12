"""ta.vfi: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volume.vfi import vfi as _calculate

from ..common import named_series


def compute(*, close, volume, length, coef, vcoef, mamode, talib):
    result = _calculate(
        close=close,
        volume=volume,
        length=length,
        coef=coef,
        vcoef=vcoef,
        mamode=mamode,
        talib=talib,
    )
    return named_series(result, "ta.vfi", "vfi")
