"""ta.td_seq: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.td_seq import td_seq as _calculate

from ..common import named_frame


def compute(*, close, asint, show_all, talib):
    result = _calculate(close=close, asint=asint, show_all=show_all, talib=talib)
    return named_frame(
        result,
        "ta.td_seq",
        {
            "TD_SEQ_UPa": "up",
            "TD_SEQ_DNa": "down",
        },
    )
