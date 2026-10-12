"""TR 的旧默认计算和显式缺失前收盘回退。"""

import numpy as np
import pandas as pd
from pandas_ta_classic.volatility.true_range import true_range as _calculate

from ..common import named_series


def compute(*, high, low, close, drift, talib, handle_na):
    if not handle_na:
        result = named_series(
            _calculate(high=high, low=low, close=close, drift=drift, talib=talib),
            "ta.true_range",
            "true_range",
        )
        if result is not None:
            result.attrs["indicator_valid"] = np.isfinite(np.column_stack([high, low, close])).all(
                axis=1
            )
        return result
    previous = close.shift(drift).to_numpy()
    h, l = high.to_numpy(), low.to_numpy()
    with np.errstate(over="ignore", invalid="ignore"):
        value = np.where(
            np.isfinite(previous),
            np.maximum.reduce([h - l, abs(h - previous), abs(l - previous)]),
            h - l,
        )
    value = np.where(np.isfinite(h) & np.isfinite(l) & (h >= l), value, np.nan)
    return pd.Series(value, index=high.index, name="true_range")
