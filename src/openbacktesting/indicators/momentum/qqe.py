"""ta.qqe: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.momentum.qqe import qqe as _calculate

from ..common import named_frame


def compute(*, close, length, smooth, factor, mamode, drift, talib):
    result = _calculate(
        close=close,
        length=length,
        smooth=smooth,
        factor=factor,
        mamode=mamode,
        drift=drift,
        talib=talib,
    )
    mode = mamode[0] if mamode != "ema" else ""
    return named_frame(
        result,
        "ta.qqe",
        {
            f"QQE{mode}_{length}_{smooth}_{factor}": "qqe",
            f"QQE{mode}_{length}_{smooth}_{factor}_RSI{mode.upper()}MA": "smoothed_rsi",
            f"QQEl{mode}_{length}_{smooth}_{factor}": "long",
            f"QQEs{mode}_{length}_{smooth}_{factor}": "short",
            f"QQEb_l{mode}_{length}_{smooth}_{factor}": "basis_long",
            f"QQEb_s{mode}_{length}_{smooth}_{factor}": "basis_short",
            f"QQEd{mode}_{length}_{smooth}_{factor}": "direction",
        },
    )
