"""ta.squeeze：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.squeeze import squeeze as _calculate

from ..common import named_frame


def compute(
    *,
    high,
    low,
    close,
    bb_length,
    bb_std,
    kc_length,
    kc_scalar,
    mom_length,
    mom_smooth,
    use_tr,
    mamode,
    talib,
):
    result = _calculate(
        high=high,
        low=low,
        close=close,
        bb_length=bb_length,
        bb_std=bb_std,
        kc_length=kc_length,
        kc_scalar=kc_scalar,
        mom_length=mom_length,
        mom_smooth=mom_smooth,
        tr=use_tr,
        mamode=mamode,
        talib=talib,
    )
    mode = "" if use_tr else "hlr"
    return named_frame(
        result,
        "ta.squeeze",
        {
            f"SQZ{mode}_{bb_length}_{bb_std}_{kc_length}_{kc_scalar}": "squeeze",
            "SQZ_ON": "on",
            "SQZ_OFF": "off",
            "SQZ_NO": "none",
        },
    )
