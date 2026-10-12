"""ta.dpo：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.trend.dpo import dpo as _calculate

from ..common import named_series


def compute(*, close, length, centered, lookahead, talib):
    result = _calculate(
        close=close, length=length, centered=centered, lookahead=lookahead, talib=talib
    )
    return named_series(result, "ta.dpo", "dpo")
