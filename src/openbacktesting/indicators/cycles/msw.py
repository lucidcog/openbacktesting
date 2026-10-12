"""ta.msw：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.cycles.msw import msw as _calculate

from ..common import named_frame


def compute(*, close, period, talib):
    result = _calculate(close=close, period=period, talib=talib)
    # 固定版本将 period=1 解释为 5；保持既有计算及命名。
    period = period if period > 1 else 5
    return named_frame(
        result,
        "ta.msw",
        {
            f"MSW_SINE_{period}": "sine",
            f"MSW_LEAD_{period}": "lead_sine",
        },
    )
