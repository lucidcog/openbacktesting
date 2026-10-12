"""Six Pivot formulas with explicit period anchors; consume only completed periods."""

import numpy as np
import pandas as pd

from ..calculus import condition
from ..types import IndicatorError


def _levels(open_, high, low, close, current_open, method):
    levels = np.full(11, np.nan)
    width = high - low
    pivot = (high + low + close) / 3
    if method == "woodie":
        pivot = (high + low + 2 * current_open) / 4
    if method == "demark":
        if close == open_:
            total = high + low + 2 * close
        elif close > open_:
            total = 2 * high + low + close
        else:
            total = high + 2 * low + close
        levels[:3] = total / 4, total / 2 - low, total / 2 - high
        return levels
    levels[0] = pivot
    if method == "fibonacci":
        for i, coefficient in enumerate((0.382, 0.618, 1), 1):
            levels[2 * i - 1 : 2 * i + 1] = pivot + width * coefficient, pivot - width * coefficient
    elif method == "camarilla":
        for i, divisor in enumerate((12, 6, 4, 2), 1):
            levels[2 * i - 1 : 2 * i + 1] = (
                close + 1.1 * width / divisor,
                close - 1.1 * width / divisor,
            )
        if low != 0:
            levels[9] = high / low * close
            levels[10] = 2 * close - levels[9]
    else:
        levels[1:5] = 2 * pivot - low, 2 * pivot - high, pivot + width, pivot - width
        if method == "classic":
            levels[5:9] = pivot + 2 * width, pivot - 2 * width, pivot + 3 * width, pivot - 3 * width
        elif method == "woodie":
            levels[5:7] = high + 2 * (pivot - low), low - 2 * (high - pivot)
            levels[7:9] = levels[5] + width, levels[6] - width
        else:
            for i in (3, 4, 5):
                levels[2 * i - 1 : 2 * i + 1] = (
                    (i - 1) * pivot + high - (i - 1) * low,
                    (i - 1) * pivot - (i - 1) * high + low,
                )
    return levels


def compute(*, open_, high, low, close, anchor, method, developing):
    if developing and method == "woodie":
        raise IndicatorError("invalid-parameter", "ta.pivot_points", "Woodie does not support developing")
    anchor = condition(anchor, "ta.pivot_points")
    if anchor.isna().any():
        raise IndicatorError("invalid-input", "ta.pivot_points", "Period anchors must not be missing")
    values = np.column_stack([open_, high, low, close])
    output = np.full((len(close), 11), np.nan)
    levels = np.full(11, np.nan)
    started = False
    complete = False
    po = ph = pl = pc = np.nan
    for i, (o, h, l, c) in enumerate(values):
        valid = np.isfinite(values[i]).all()
        if developing:
            valid = valid and h >= l
        if anchor.iloc[i] == 1:
            if started and complete and (method != "woodie" or np.isfinite(o)):
                levels = _levels(po, ph, pl, pc, o, method)
            else:
                levels = np.full(11, np.nan)
            started, complete = True, valid
            po, ph, pl, pc = o, h, l, c
        elif started:
            complete &= valid
            ph, pl, pc = max(ph, h), min(pl, l), c
        if developing:
            levels = (
                _levels(po, ph, pl, pc, o, method) if started and complete else np.full(11, np.nan)
            )
        output[i] = levels
    return pd.DataFrame(
        output,
        index=close.index,
        columns=["p", "r1", "s1", "r2", "s2", "r3", "s3", "r4", "s4", "r5", "s5"],
    )
