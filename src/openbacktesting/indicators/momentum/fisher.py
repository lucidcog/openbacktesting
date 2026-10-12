"""ta.fisher：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.fisher import fisher as _calculate

from ..common import named_frame


def compute(*, high, low, length, signal, talib):
    result = _calculate(high=high, low=low, length=length, signal=signal, talib=talib)
    return named_frame(
        result,
        "ta.fisher",
        {
            f"FISHERT_{length}_{signal}": "fisher",
            f"FISHERTs_{length}_{signal}": "signal",
        },
    )
