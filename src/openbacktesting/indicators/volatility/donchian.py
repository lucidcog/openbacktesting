"""ta.donchian: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.volatility.donchian import donchian as _calculate

from ..common import named_frame


def compute(*, high, low, lower_length, upper_length, talib):
    result = _calculate(
        high=high, low=low, lower_length=lower_length, upper_length=upper_length, talib=talib
    )
    return named_frame(
        result,
        "ta.donchian",
        {
            f"DCL_{lower_length}_{upper_length}": "lower",
            f"DCM_{lower_length}_{upper_length}": "middle",
            f"DCU_{lower_length}_{upper_length}": "upper",
        },
    )
