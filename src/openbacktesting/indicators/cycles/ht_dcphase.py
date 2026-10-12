"""ta.ht_dcphase：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.cycles.ht_dcphase import ht_dcphase as _calculate

from ..common import named_series


def compute(*, close, talib):
    result = _calculate(close=close, talib=talib)
    return named_series(result, "ta.ht_dcphase", "ht_dcphase")
