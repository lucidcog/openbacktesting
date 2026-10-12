"""ta.mama: Computation wrapper for the pinned dependency with canonical outputs."""

from pandas_ta_classic.overlap.mama import mama as _calculate

from ..common import named_frame


def compute(*, close, fastlimit, slowlimit, talib):
    result = _calculate(close=close, fastlimit=fastlimit, slowlimit=slowlimit, talib=talib)
    return named_frame(
        result,
        "ta.mama",
        {
            f"MAMA_{fastlimit}_{slowlimit}": "mama",
            f"FAMA_{fastlimit}_{slowlimit}": "fama",
        },
    )
