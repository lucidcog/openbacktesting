"""ta.eri：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.eri import eri as _calculate

from ..common import named_frame


def compute(*, high, low, close, length, talib):
    result = _calculate(high=high, low=low, close=close, length=length, talib=talib)
    return named_frame(
        result,
        "ta.eri",
        {
            f"BULLP_{length}": "bull_power",
            f"BEARP_{length}": "bear_power",
        },
    )
