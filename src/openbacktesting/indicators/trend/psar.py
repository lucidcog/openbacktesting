"""ta.psar: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.psar import psar as _calculate

from ..common import named_frame


def compute(*, high, low, close, af0, af, max_af, talib):
    result = _calculate(high=high, low=low, close=close, af0=af0, af=af, max_af=max_af, talib=talib)
    return named_frame(
        result,
        "ta.psar",
        {
            f"PSARl_{af0}_{max_af}": "long",
            f"PSARs_{af0}_{max_af}": "short",
            f"PSARaf_{af0}_{max_af}": "acceleration",
            f"PSARr_{af0}_{max_af}": "reversal",
        },
    )
