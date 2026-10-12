"""ta.natr：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volatility.natr import natr as _calculate

from ..common import named_series


def compute(*, high, low, close, length, scalar, mamode, drift, talib):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        length=length,
        scalar=scalar,
        mamode=mamode,
        drift=drift,
        talib=talib,
    )
    return named_series(result, "ta.natr", "natr")
