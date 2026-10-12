"""Weighted accumulation with explicit condition anchors; no inference of sessions or higher timeframes."""

from math import isfinite, sqrt

import numpy as np
import pandas as pd

from ..calculus import condition
from ..types import IndicatorError


def _calculate(*, source, volume, anchor, indicator, stdev_mult):
    reset = condition(anchor, indicator)
    if reset.isna().any():
        raise IndicatorError("invalid-input", indicator, "Anchors must not be missing")
    if ((volume < 0) & np.isfinite(volume)).any():
        raise IndicatorError("invalid-input", indicator, "Volume must not be negative")
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
                # Equivalent to weighted Welford central-moment increments; all factors are nonnegative, avoiding negative variance from cancellation.
                moment += delta * delta * (weight / total) * v
            weight = total
        if weight == 0:
            continue
        spread = stdev_mult * sqrt(moment / weight)
        row = mean, mean - spread, mean + spread
        if not all(isfinite(value) for value in (*row, weight, moment)):
            raise IndicatorError("calculation-failed", indicator, "VWAP accumulation or output overflow")
        values[i] = row
    return pd.DataFrame(values, index=source.index, columns=["vwap", "lower", "upper"])


def compute(*, source, volume, anchor):
    return _calculate(
        source=source, volume=volume, anchor=anchor, indicator="ta.anchored_vwap", stdev_mult=0.0
    )["vwap"]
