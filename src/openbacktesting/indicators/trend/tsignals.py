"""ta.tsignals：固定依赖的计算封装与规范输出。"""

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
