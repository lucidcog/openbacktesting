"""ta.alma：固定依赖的计算封装与规范输出。"""

import numpy as np
import pandas as pd
from pandas_ta_classic.overlap.alma import alma as _calculate

from ..common import named_series


def compute(*, close, length, sigma, distribution_offset, talib, floor):
    if floor:
        center = np.floor(distribution_offset * (length - 1))
        distance = np.arange(length, dtype=float) - center
        # 中心为整数，至少一个权重精确为 1；极端 sigma 其余权重可安全下溢。
        with np.errstate(over="ignore", under="ignore"):
            scaled = distance * (sigma / length)
            weights = np.exp(-0.5 * scaled * scaled)
        weights /= weights.sum()
        output = np.full(len(close), np.nan)
        if len(close) >= length:
            windows = np.lib.stride_tricks.sliding_window_view(close.to_numpy(), length)
            with np.errstate(invalid="ignore", over="ignore"):
                values = windows @ weights[::-1]
            output[length - 1 :] = np.where(np.isfinite(windows).all(axis=1), values, np.nan)
        return pd.Series(output, index=close.index, name="alma")
    result = _calculate(
        close=close,
        length=length,
        sigma=sigma,
        distribution_offset=distribution_offset,
        talib=talib,
    )
    return named_series(result, "ta.alma", "alma")
