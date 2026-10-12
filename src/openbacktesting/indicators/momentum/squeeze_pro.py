"""ta.squeeze_pro：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.momentum.squeeze_pro import squeeze_pro as _calculate

from ..common import named_frame


def compute(
    *,
    high,
    low,
    close,
    bb_length,
    bb_std,
    kc_length,
    kc_scalar_wide,
    kc_scalar_normal,
    kc_scalar_narrow,
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
        kc_scalar_wide=kc_scalar_wide,
        kc_scalar_normal=kc_scalar_normal,
        kc_scalar_narrow=kc_scalar_narrow,
        mom_length=mom_length,
        mom_smooth=mom_smooth,
        tr=use_tr,
        mamode=mamode,
        talib=talib,
    )
    mode = "" if use_tr else "hlr"
    return named_frame(
        result,
        "ta.squeeze_pro",
        {
            f"SQZPRO{mode}_{bb_length}_{bb_std}_{kc_length}_{float(kc_scalar_wide)}_{float(kc_scalar_normal)}_{float(kc_scalar_narrow)}": "squeeze",
            "SQZPRO_ON_WIDE": "on_wide",
            "SQZPRO_ON_NORMAL": "on_normal",
            "SQZPRO_ON_NARROW": "on_narrow",
            "SQZPRO_OFF": "off",
            "SQZPRO_NO": "none",
        },
    )
