"""ta.mavp：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.overlap.mavp import mavp as _calculate

from ..common import named_series


def compute(*, close, periods, minperiod, maxperiod, mamode, talib):
    result = _calculate(
        close=close,
        periods=periods,
        minperiod=minperiod,
        maxperiod=maxperiod,
        mamode=mamode,
        talib=talib,
    )
    return named_series(result, "ta.mavp", "mavp")
