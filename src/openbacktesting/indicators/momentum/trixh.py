"""ta.trixh：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.trixh import trixh as _calculate

from ..common import named_frame


def compute(*, close, length, signal, scalar, drift, talib):
    result = _calculate(
        close=close, length=length, signal=signal, scalar=scalar, drift=drift, talib=talib
    )
    return named_frame(
        result,
        "ta.trixh",
        {
            f"TRIX_{length}_{signal}": "trix",
            f"TRIXs_{length}_{signal}": "signal",
            f"TRIXh_{length}_{signal}": "histogram",
        },
    )
