"""ta.drawdown：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.performance.drawdown import drawdown as _calculate

from ..common import named_frame


def compute(*, close, talib):
    result = _calculate(close=close, talib=talib)
    return named_frame(
        result,
        "ta.drawdown",
        {
            "DD": "absolute",
            "DD_PCT": "percent",
            "DD_LOG": "logarithmic",
        },
    )
