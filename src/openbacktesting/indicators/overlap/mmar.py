"""ta.mmar: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.mmar import mmar as _calculate

from ..common import named_frame


def compute(*, close, length, talib):
    result = _calculate(close=close, length=length, talib=talib)
    return named_frame(
        result,
        "ta.mmar",
        {
            f"MMAR_{length}": "ma1",
            f"MMAR_{length + 5}": "ma2",
            f"MMAR_{length + 10}": "ma3",
            f"MMAR_{length + 15}": "ma4",
            f"MMAR_{length + 20}": "ma5",
            f"MMAR_{length + 25}": "ma6",
        },
    )
