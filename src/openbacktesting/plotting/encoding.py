"""冻结与严格 JSON 编码；只接收已完成的纯值事实。"""

from __future__ import annotations

import json
import math
from numbers import Integral

import numpy as np
import pandas as pd

from openbacktesting.plotting.types import PlottingError, _Snapshot


def scalar(value):
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, Integral):
        value = int(value)
        return value if abs(value) <= 2**53 - 1 else str(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, str):
        return value
    raise PlottingError("invalid-value", f"不支持的纯值类型 {type(value).__name__}")


def axis(index):
    if isinstance(index, pd.DatetimeIndex):
        if index.tz is not None:
            return {
                "id": "bars",
                "kind": "utc-ns",
                "timezone": str(index.tz),
                "labels": [str(v.value) for v in index],
            }
        return {
            "id": "bars",
            "kind": "naive-datetime",
            "timezone": None,
            "labels": [v.isoformat() for v in index],
        }
    return {
        "id": "bars",
        "kind": "ordinal",
        "timezone": None,
        "labels": [str(scalar(v)) for v in index],
    }


def numeric(values, valid, ready):
    finite = np.isfinite(values)
    return {
        "values": [scalar(v) for v in values],
        "valid": (valid & finite).tolist(),
        "ready": ready.tolist(),
        "missing": [None if ok else "non-finite" for ok in finite],
    }


def facts(table, columns):
    return [
        {key: scalar(value) for key, value in zip(columns, row)}
        for row in table.loc[:, columns].itertuples(index=False, name=None)
    ]


def freeze(payload, byte_limit):
    return _Snapshot(
        "1.1.0",
        json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")),
        byte_limit,
    )


def export_result(result: pd.Series) -> dict:
    """从成功回测的冻结快照返回独立 PlottingResult 字典，不读取策略实例。

    Args:
        result: 开启采集的 Backtest.run 或 runtime.run 结果。

    Returns:
        可经 json.dumps(..., allow_nan=False) 编码的独立字典。

    Raises:
        PlottingError: 快照缺失、类型或版本不支持，或超过导出字节预算。
    """
    snapshot = getattr(result, "attrs", {}).get("plotting_result")
    if not isinstance(snapshot, _Snapshot):
        raise PlottingError("missing-snapshot", "需要开启采集且成功完成的回测结果")
    if snapshot.version not in ("1.0.0", "1.1.0"):
        raise PlottingError("unsupported-version", snapshot.version)
    if snapshot.byte_length > snapshot.byte_limit:
        raise PlottingError("PlottingLimitExceeded", "bytes 超过导出预算")
    payload = json.loads(snapshot.payload)
    if payload.get("schemaVersion") != snapshot.version:
        raise PlottingError("unsupported-version", "快照与载荷版本不一致")
    return payload
