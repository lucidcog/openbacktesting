"""ta.ht_phasor: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.cycles.ht_phasor import ht_phasor as _calculate

from ..common import named_frame


def compute(*, close, talib):
    result = _calculate(close=close, talib=talib)
    return named_frame(
        result,
        "ta.ht_phasor",
        {
            "HT_PHASOR_INPHASE": "inphase",
            "HT_PHASOR_QUAD": "quadrature",
        },
    )
