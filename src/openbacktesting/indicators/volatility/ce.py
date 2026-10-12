"""ta.ce: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volatility.ce import ce as _calculate

from ..common import named_frame


def compute(*, high, low, close, length, multiplier, mamode, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        length=length,
        multiplier=multiplier,
        mamode=mamode,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.ce",
        {
            f"CE_L_{length}_{multiplier}": "long",
            f"CE_S_{length}_{multiplier}": "short",
        },
    )
