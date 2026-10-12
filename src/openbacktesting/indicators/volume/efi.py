"""ta.efi：固定依赖的计算封装与规范输出。"""

from pandas_ta_classic.volume.efi import efi as _calculate

from ..common import named_series


def compute(*, close, volume, length, mamode, drift, talib):
    result = _calculate(
        close=close, volume=volume, length=length, mamode=mamode, drift=drift, talib=talib
    )
    return named_series(result, "ta.efi", "efi")
