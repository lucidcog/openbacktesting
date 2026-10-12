"""ta.cpr：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.trend.cpr import cpr as _calculate

from ..common import named_frame


def compute(
    *,
    open_,
    high,
    low,
    close,
    volume,
    method,
    timeframe,
    interval,
    levels,
    width_analysis,
    price_position,
    virgin_cpr,
    lookahead,
    talib,
):
    result = _calculate(
        open_=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        method=method,
        timeframe=timeframe,
        interval=interval,
        levels=levels,
        width_analysis=width_analysis,
        price_position=price_position,
        virgin_cpr=virgin_cpr,
        lookahead=lookahead,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.cpr",
        {
            "CPR_TC": "top",
            "CPR_PIVOT": "pivot",
            "CPR_BC": "bottom",
            "CPR_R1": "r1",
            "CPR_R2": "r2",
            "CPR_S1": "s1",
            "CPR_S2": "s2",
            "CPR_WIDTH": "width",
            "CPR_WIDTH_PCT": "width_percent",
            "CPR_WIDTH_CLASS": "width_class",
            "CPR_POSITION": "position",
        },
    )
