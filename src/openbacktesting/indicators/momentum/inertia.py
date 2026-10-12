"""ta.inertia：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.inertia import inertia as _calculate

from ..common import named_series


def compute(*, close, high, low, length, rvi_length, scalar, refined, thirds, mamode, drift, talib):
    result = _calculate(
        close=close,
        high=high,
        low=low,
        length=length,
        rvi_length=rvi_length,
        scalar=scalar,
        refined=refined,
        thirds=thirds,
        mamode=mamode,
        drift=drift,
        talib=talib,
    )
    return named_series(result, "ta.inertia", "inertia")
