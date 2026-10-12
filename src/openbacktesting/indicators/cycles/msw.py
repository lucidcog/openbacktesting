"""ta.msw: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.cycles.msw import msw as _calculate

from ..common import named_frame


def compute(*, close, period, talib):
    result = _calculate(close=close, period=period, talib=talib)
    # The pinned version interprets period=1 as 5; preserve existing calculations and naming.
    period = period if period > 1 else 5
    return named_frame(
        result,
        "ta.msw",
        {
            f"MSW_SINE_{period}": "sine",
            f"MSW_LEAD_{period}": "lead_sine",
        },
    )
