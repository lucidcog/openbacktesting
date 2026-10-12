"""ta.hwc：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volatility.hwc import hwc as _calculate

from ..common import named_frame


def compute(*, close, na, nb, nc, nd, scalar, channel_eval, talib):
    result = _calculate(
        close=close,
        na=na,
        nb=nb,
        nc=nc,
        nd=nd,
        scalar=scalar,
        channel_eval=channel_eval,
        talib=talib,
    )
    return named_frame(
        result,
        "ta.hwc",
        {
            "HWM": "middle",
            "HWU": "upper",
            "HWL": "lower",
        },
    )
