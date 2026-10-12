"""ta.ht_trendmode：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.cycles.ht_trendmode import ht_trendmode as _calculate

from ..common import named_series


def compute(*, close, talib):
    result = _calculate(close=close, talib=talib)
    return named_series(result, "ta.ht_trendmode", "ht_trendmode")
