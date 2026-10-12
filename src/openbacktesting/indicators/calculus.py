"""本地指标共享的有限历史数学；不依赖登记、缓存或策略。"""

import numpy as np
import pandas as pd

from .types import IndicatorError


def clean(source):
    return source.astype(float).where(np.isfinite(source))


def segments(valid):
    """返回连续有效区段，缺失后的递归状态必须重新建立。"""
    edges = np.diff(np.r_[False, valid, False].astype(np.int8))
    return zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))


def average(source, length, *, alpha=None, seeded=True):
    """SMA种子或首值种子的递归平均；缺失后重新预热。"""
    source = clean(source)
    out = np.full(len(source), np.nan)
    alpha = 2 / (length + 1) if alpha is None else alpha
    for start, end in segments(source.notna().to_numpy()):
        part = source.iloc[start:end].to_numpy(copy=True)
        skip = length - 1 if seeded else 0
        if len(part) <= skip:
            continue
        if seeded:
            part[skip] = part[:length].mean()
        out[start + skip : end] = pd.Series(part[skip:]).ewm(alpha=alpha, adjust=False).mean()
    return pd.Series(out, index=source.index)


def ratio(numerator, denominator):
    return numerator / denominator.where(denominator != 0)


def atr(high, low, close, length):
    previous = clean(close).shift(1)
    ranges = np.maximum.reduce(
        [(clean(high) - clean(low)).to_numpy(), (high - previous).abs(), (low - previous).abs()]
    )
    return average(pd.Series(ranges, index=close.index), length, alpha=1 / length)


def strength(delta, length):
    gains = average(delta.clip(lower=0), length, alpha=1 / length)
    losses = average(-delta.clip(upper=0), length, alpha=1 / length)
    total = gains + losses
    return ratio(100 * gains, total).mask(total == 0, 50.0)


def condition(source, indicator):
    source = clean(source)
    if not source.dropna().isin([0, 1]).all():
        raise IndicatorError("invalid-input", indicator, "条件输入只允许0、1或缺失")
    return source


def pattern_result(calculate, indicator, inputs, minimum, **options):
    """按有效OHLC区段调用原生形态，独立保留整数分值和有效掩码。"""
    frame = pd.DataFrame(inputs)
    values = np.zeros(len(frame), dtype=np.int16)
    valid = np.zeros(len(frame), dtype=bool)
    for start, end in segments(np.isfinite(frame.to_numpy()).all(axis=1)):
        if end - start < minimum:
            continue
        part = frame.iloc[start:end]
        result = calculate(**{key: part[key] for key in inputs}, **options)
        values[start:end] = result.to_numpy(dtype=np.int16)
        valid[start + minimum - 1 : end] = True
    result = pd.Series(values, index=frame.index, name=indicator)
    result.attrs["indicator_valid"] = valid
    return result
