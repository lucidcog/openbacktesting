"""ta.rvgi：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.rvgi import rvgi as _calculate

from ..common import named_frame


def compute(*, open_, high, low, close, length, swma_length, talib):
    result = _calculate(
        open_=open_,
        high=high,
        low=low,
        close=close,
        length=length,
        swma_length=swma_length,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.rvgi",
        {
            f"RVGIh_{length}_{swma_length}": "histogram",
            f"RVGI_{length}_{swma_length}": "rvgi",
            f"RVGIs_{length}_{swma_length}": "signal",
        },
    )
