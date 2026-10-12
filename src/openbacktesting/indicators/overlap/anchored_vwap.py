"""明确条件锚点的加权累计；不推断交易时段或高周期。"""

from math import isfinite, sqrt

import numpy as np
import pandas as pd

from ..calculus import condition
from ..types import IndicatorError


def _calculate(*, source, volume, anchor, indicator, stdev_mult):
    reset = condition(anchor, indicator)
    if reset.isna().any():
        raise IndicatorError("invalid-input", indicator, "锚点不能缺失")
    if ((volume < 0) & np.isfinite(volume)).any():
        raise IndicatorError("invalid-input", indicator, "成交量不能为负")
    values = np.full((len(source), 3), np.nan)
    started = False
    weight = mean = moment = 0.0
    for i, (x, v, flag) in enumerate(zip(source, volume, reset)):
        if flag == 1:
            started = True
            weight = mean = moment = 0.0
        if not started or not (isfinite(x) and isfinite(v)):
            continue
        if v > 0:
            total = weight + v
            if weight == 0:
                mean = x
            else:
                delta = x - mean
                mean += delta * (v / total)
                # 等价于加权 Welford 的中心矩增量，各因子非负，无抵消负方差。
                moment += delta * delta * (weight / total) * v
            weight = total
        if weight == 0:
            continue
        spread = stdev_mult * sqrt(moment / weight)
        row = mean, mean - spread, mean + spread
        if not all(isfinite(value) for value in (*row, weight, moment)):
            raise IndicatorError("calculation-failed", indicator, "VWAP 累计或输出溢出")
        values[i] = row
    return pd.DataFrame(values, index=source.index, columns=["vwap", "lower", "upper"])


def compute(*, source, volume, anchor):
    return _calculate(
        source=source, volume=volume, anchor=anchor, indicator="ta.anchored_vwap", stdev_mult=0.0
    )["vwap"]
