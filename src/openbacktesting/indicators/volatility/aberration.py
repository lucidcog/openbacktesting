"""ta.aberration: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volatility.aberration import aberration as _calculate

from ..common import named_frame


def compute(*, high, low, close, length, atr_length, talib):
    result = _calculate(
        high=high, low=low, close=close, length=length, atr_length=atr_length, talib=talib
    )
    return named_frame(
        result,
        "ta.aberration",
        {
            f"ABER_ZG_{length}_{atr_length}": "middle",
            f"ABER_SG_{length}_{atr_length}": "upper",
            f"ABER_XG_{length}_{atr_length}": "lower",
            f"ABER_ATR_{length}_{atr_length}": "atr",
        },
    )
