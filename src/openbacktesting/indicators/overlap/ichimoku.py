"""ta.ichimoku：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.ichimoku import ichimoku as _calculate

from ..common import named_frame


def compute(
    *,
    high,
    low,
    close,
    tenkan,
    kijun,
    senkou,
    include_chikou,
    lookahead,
    as_dataframe,
    append_span,
    talib,
):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        tenkan=tenkan,
        kijun=kijun,
        senkou=senkou,
        include_chikou=include_chikou,
        lookahead=lookahead,
        as_dataframe=as_dataframe,
        append_span=append_span,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.ichimoku",
        {
            f"ISA_{tenkan}": "span_a",
            f"ISB_{kijun}": "span_b",
            f"ITS_{tenkan}": "tenkan",
            f"IKS_{kijun}": "kijun",
        },
    )
