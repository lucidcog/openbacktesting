"""ta.ha：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.candles.ha import ha as _calculate

from ..common import named_frame


def compute(*, open_, high, low, close, talib):
    result = _calculate(open_=open_, high=high, low=low, close=close, talib=talib)
    return named_frame(
        result,
        "ta.ha",
        {
            "HA_open": "open",
            "HA_high": "high",
            "HA_low": "low",
            "HA_close": "close",
        },
    )
