"""ta.brar：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.brar import brar as _calculate

from ..common import named_frame


def compute(*, open_, high, low, close, length, scalar, drift, talib):
    result = _calculate(
        open_=open_,
        high=high,
        low=low,
        close=close,
        length=length,
        scalar=scalar,
        drift=drift,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.brar",
        {
            f"AR_{length}": "ar",
            f"BR_{length}": "br",
        },
    )
