"""ta.cdl_z: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.candles.cdl_z import cdl_z as _calculate

from ..common import named_frame


def compute(*, open_, high, low, close, length, ddof, full, talib):
    result = _calculate(
        open_=open_,
        high=high,
        low=low,
        close=close,
        length=length,
        ddof=ddof,
        full=full,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.cdl_z",
        {
            f"open_Z_{length}_{ddof or 1}": "open",
            f"high_Z_{length}_{ddof or 1}": "high",
            f"low_Z_{length}_{ddof or 1}": "low",
            f"close_Z_{length}_{ddof or 1}": "close",
        },
    )
