"""ta.rvi：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volatility.rvi import rvi as _calculate

from ..common import named_series


def compute(*, close, high, low, length, scalar, refined, thirds, mamode, drift, talib):
    result = _calculate(
        close=close,
        high=high,
        low=low,
        length=length,
        scalar=scalar,
        refined=refined,
        thirds=thirds,
        mamode=mamode,
        drift=drift,
        talib=talib,
    )
    return named_series(result, "ta.rvi", "rvi")
