"""ta.vortex: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.vortex import vortex as _calculate

from ..common import named_frame


def compute(*, high, low, close, length, drift, talib):
    result = _calculate(high=high, low=low, close=close, length=length, drift=drift, talib=talib)
    return named_frame(
        result,
        "ta.vortex",
        {
            f"VTXP_{length}": "positive",
            f"VTXM_{length}": "negative",
        },
    )
