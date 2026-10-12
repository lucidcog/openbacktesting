"""ta.kc：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volatility.kc import kc as _calculate

from ..common import named_frame


def compute(*, high, low, close, length, scalar, mamode, talib, use_true_range):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        length=length,
        scalar=scalar,
        mamode=mamode,
        talib=talib,
        tr=use_true_range,
    )
    return named_frame(
        result,
        "ta.kc",
        {
            f"KCL{mamode[0]}_{length}_{float(scalar)}": "lower",
            f"KCB{mamode[0]}_{length}_{float(scalar)}": "middle",
            f"KCU{mamode[0]}_{length}_{float(scalar)}": "upper",
        },
    )
