"""ta.tsignals: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.trend.tsignals import tsignals as _calculate

from ..common import named_frame


def compute(*, trend, asbool, trade_offset, drift, trend_reset, talib):
    result = _calculate(
        trend=trend,
        asbool=asbool,
        trade_offset=trade_offset,
        drift=drift,
        trend_reset=trend_reset,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.tsignals",
        {
            "TS_Trends": "trend",
            "TS_Trades": "trades",
            "TS_Entries": "entries",
            "TS_Exits": "exits",
        },
    )
