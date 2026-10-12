"""cdl_morningstar：固定原生形态与独立有效掩码。"""

from pandas_ta_classic.candles.cdl_morningstar import cdl_morningstar as _calculate

from ..calculus import pattern_result


def compute(*, open_, high, low, close, penetration, talib):
    return pattern_result(
        _calculate,
        "cdl_morningstar",
        {"open_": open_, "high": high, "low": low, "close": close},
        13,
        penetration=penetration,
    )
