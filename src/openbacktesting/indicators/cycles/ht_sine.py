"""ta.ht_sine：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.cycles.ht_sine import ht_sine as _calculate

from ..common import named_frame


def compute(*, close, talib):
    result = _calculate(close=close, talib=talib)
    return named_frame(
        result,
        "ta.ht_sine",
        {
            "HT_SINE": "sine",
            "HT_LEADSINE": "lead_sine",
        },
    )
