"""cdl_eveningstar：固定原生形态与独立有效掩码。"""

from pandas_ta_classic.candles.cdl_eveningstar import cdl_eveningstar as _calculate

from ..calculus import pattern_result


def compute(*, open_, high, low, close, penetration, talib):
    return pattern_result(
        _calculate,
        "cdl_eveningstar",
        {"open_": open_, "high": high, "low": low, "close": close},
        13,
        penetration=penetration,
    )
