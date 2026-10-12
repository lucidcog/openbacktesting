"""ta.stc：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.stc import stc as _calculate

from ..common import named_frame


def compute(*, close, tclength, fast, slow, factor, talib):
    result = _calculate(
        close=close, tclength=tclength, fast=fast, slow=slow, factor=factor, talib=talib
    )
    return named_frame(
        result,
        "ta.stc",
        {
            f"STC_{tclength}_{fast}_{slow}_{factor}": "stc",
            f"STCmacd_{tclength}_{fast}_{slow}_{factor}": "macd",
            f"STCstoch_{tclength}_{fast}_{slow}_{factor}": "stochastic",
        },
    )
