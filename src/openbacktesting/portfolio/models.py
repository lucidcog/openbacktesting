"""Strict plain-value encoding, metrics, and immutable snapshots without runtime objects."""

import math

import numpy as np
import pandas as pd


def time_ref(value):
    if isinstance(value, pd.Timestamp):
        return {
            "kind": "aware" if value.tzinfo else "naive",
            "value": str(value.as_unit("ns").value),
        }
    return {"kind": "ordinal", "value": str(value)}


def plain(value):
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return time_ref(value)
    if isinstance(value, pd.Timedelta):
        return str(value.value)
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, int) and not isinstance(value, bool) and abs(value) > 2**53 - 1:
        return str(value)
    if isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError(f"Portfolio does not support plain-value encoding: {type(value).__name__}")


def metric(
    value,
    unit="ratio",
    *,
    method="openbacktesting_portfolio_v1",
    reason=None,
    status=None,
    sample=None,
    reference=None,
):
    value = plain(value)
    return {
        "value": value,
        "unit": unit,
        "methodId": method,
        "status": status or ("ok" if value is not None else "undefined"),
        "reason": (reason or "undefined_value") if value is None else (reason if status else None),
        "sampleCount": sample,
        "reference": reference,
    }


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None
