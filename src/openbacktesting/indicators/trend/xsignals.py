"""ta.xsignals: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.xsignals import xsignals as _calculate

from ..common import named_frame


def compute(*, signal, xa, xb, above, long, asbool, trade_offset, trend_reset, talib):
    result = _calculate(
        signal=signal,
        xa=xa,
        xb=xb,
        above=above,
        long=long,
        asbool=asbool,
        trade_offset=trade_offset,
        trend_reset=trend_reset,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.xsignals",
        {
            "TS_Trends": "trend",
            "TS_Trades": "trades",
            "TS_Entries": "entries",
            "TS_Exits": "exits",
        },
    )
