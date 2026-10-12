"""ta.pdist：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volatility.pdist import pdist as _calculate

from ..common import named_series


def compute(*, open_, high, low, close, drift, talib):
    result = _calculate(open_=open_, high=high, low=low, close=close, drift=drift, talib=talib)
    return named_series(result, "ta.pdist", "pdist")
