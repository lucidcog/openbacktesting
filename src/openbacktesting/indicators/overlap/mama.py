"""ta.mama：固定依赖的计算封装与规范输出。"""

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
