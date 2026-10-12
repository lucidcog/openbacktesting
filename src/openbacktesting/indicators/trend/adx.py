"""ta.adx：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.trend.adx import adx as _calculate

from ..common import named_frame


def compute(*, high, low, close, length, lensig, scalar, mamode, drift, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        length=length,
        lensig=lensig,
        scalar=scalar,
        mamode=mamode,
        drift=drift,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.adx",
        {
            f"ADX_{lensig}": "adx",
            f"DMP_{length}": "positive",
            f"DMN_{length}": "negative",
        },
    )
