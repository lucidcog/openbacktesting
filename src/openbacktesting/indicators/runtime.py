"""内置指标目录、纯计算入口及有界计算复用。"""

from __future__ import annotations

import json
from collections import OrderedDict
from concurrent.futures import Future
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from importlib.metadata import version
from threading import RLock
from uuid import uuid4

import numpy as np
import pandas as pd

from .common import SPECS, to_arrays
from .registry import execute, validate_backend
from .types import IndicatorCursor, IndicatorError, IndicatorHandle

DEFAULT_CACHE_BYTES = 64 * 1024 * 1024
_CATALOG = {spec.id: spec for spec in SPECS}
_COLUMNS = {"open_": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}


def catalog():
    """返回全部已审核定义的元组，包括不可调用的延期项。

    Returns:
        tuple: 指标定义；调用前检查 status，数量随审核目录变化。
    """
    return tuple(_CATALOG.values())


def describe(indicator):
    """按稳定 ID 查询指标定义，不执行计算。

    Args:
        indicator: 目录中的完整 ID，例如 ta.ema。

    Returns:
        IndicatorSpec: 参数域、输出、状态及语义版本定义。

    Raises:
        IndicatorError: ID 不存在时 code 为 unknown-indicator。
    """
    try:
        return _CATALOG[indicator]
    except KeyError as error:
        raise IndicatorError("unknown-indicator", indicator, "未登记指标") from error


class IndicatorCache:
    """预算是缓存保留量；活跃策略持有量不受这个预算限制。"""

    def __init__(self, budget=DEFAULT_CACHE_BYTES):
        if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
            raise ValueError("缓存预算必须是非负整数")
        self.budget = budget
        self.bytes = 0
        self.hits = self.misses = 0
        self._entries = OrderedDict()
        self._pending = {}
        self._lock = RLock()

    def get(self, key, calculate):
        """使用 key 查找缓存，否则执行 calculate；同键并发合并，失败不缓存，返回只读模板。"""
        if not self.budget:
            self.misses += 1
            return calculate()
        with self._lock:
            if key in self._entries:
                self.hits += 1
                self._entries.move_to_end(key)
                return self._entries[key][0]
            if key in self._pending:
                future = self._pending[key]
                owner = False
            else:
                future = self._pending[key] = Future()
                self.misses += 1
                owner = True
        if not owner:
            return future.result()
        try:
            value = calculate()
            size = (
                value._values.nbytes
                + value._valid.nbytes
                + value._ready.nbytes
                + value._gating.nbytes
                + value._opts["index"].nbytes
            )
            with self._lock:
                if self.budget and size <= self.budget:
                    while self.bytes + size > self.budget:
                        _, (_, removed) = self._entries.popitem(last=False)
                        self.bytes -= removed
                    self._entries[key] = (value, size)
                    self.bytes += size
                future.set_result(value)
            return value
        except BaseException as error:
            future.set_exception(error)
            raise
        finally:
            with self._lock:
                del self._pending[key]

    def clear(self):
        """清空保留条目并归零保留字节数；不撤销活跃结果引用。"""
        with self._lock:
            self._entries.clear()
            self.bytes = 0


def _data_identity(frame):
    digest = sha256(pd.util.hash_pandas_object(frame, index=True).values.tobytes())
    digest.update(
        repr(
            (
                tuple(frame.columns),
                tuple(map(str, frame.dtypes)),
                str(frame.index.dtype),
                frame.index.name,
            )
        ).encode()
    )
    return digest.hexdigest()


def _prepare_inputs(spec, frame, inputs, cursor):
    if not isinstance(frame, pd.DataFrame) or not frame.index.is_unique:
        raise IndicatorError("index-mismatch", spec.id, "输入必须为唯一索引 DataFrame")
    mapping = dict(inputs or {})
    if mapping.keys() - set(spec.inputs):
        raise IndicatorError("missing-input", spec.id, "输入映射包含未声明字段")
    columns = {}
    dtypes = {}
    defaults = dict(spec.input_defaults)
    for name in spec.inputs:
        source = mapping.get(name, defaults.get(name, _COLUMNS.get(name, name)))
        if isinstance(source, IndicatorHandle):
            if cursor is None or source._cursor is not cursor or source.ndim != 1:
                raise IndicatorError("index-mismatch", spec.id, "指标输入必须来自本运行的单通道")
            series = source.s.where(source.valid)
        else:
            if not isinstance(source, str) or source not in frame:
                raise IndicatorError("missing-input", spec.id, f"缺少输入: {name}")
            series = frame[source]
        if not series.index.equals(frame.index):
            raise IndicatorError("index-mismatch", spec.id, "输入索引不一致")
        if not pd.api.types.is_numeric_dtype(series.dtype):
            raise IndicatorError("missing-input", spec.id, f"{name} 必须为数值")
        dtypes[name] = str(series.dtype)
        columns[name] = series.to_numpy(dtype=float, copy=False)
    prepared = pd.DataFrame(columns, index=frame.index, copy=True)
    prepared.attrs["input_dtypes"] = dtypes
    return prepared


def compute(
    indicator,
    frame,
    *,
    parameters=None,
    backend=None,
    inputs=None,
    cache=None,
    cursor=None,
    required_outputs=None,
):
    """对显式行情批量计算已审核指标，返回只读结果句柄。

    Args:
        indicator: 完整目录 ID。
        frame: pandas DataFrame；索引和输入必须满足指标契约。
        parameters: 参数映射；未知键、非法类型和关系均拒绝。
        backend: 后端标识；None 使用目录默认值，不静默回退。
        inputs: 指标输入到行情列名或同运行单通道的映射。
        cache: 可选 IndicatorCache；None 每次重新计算。
        cursor: 框架内部运行游标；独立计算保留 None。
        required_outputs: 必要输出规范名；空列表关闭预热门控。

    Returns:
        IndicatorHandle: 单通道或多通道句柄，具有 valid/ready 与来源 metadata。

    Raises:
        IndicatorError: ID、参数、后端、输入、输出或计算失败。
    """
    spec = describe(indicator)
    parameters = spec.normalize(dict(parameters or {}))
    backend = spec.default_backend if backend is None else backend
    binding = validate_backend(spec, backend)
    if spec.status != "available":
        raise IndicatorError("unavailable-indicator", indicator, spec.reason)
    required = spec.outputs if spec.required is None else spec.required
    required = tuple(required if required_outputs is None else required_outputs)
    if not set(required) <= set(spec.outputs):
        raise IndicatorError("output-contract", indicator, "未知必要通道")
    data = _prepare_inputs(spec, frame, inputs, cursor)
    metadata = {
        "id": indicator,
        "semantic_version": spec.version,
        "implementation_version": binding.implementation_version,
        "parameters": parameters,
        "data_identity": _data_identity(data),
        "input_dtypes": data.attrs["input_dtypes"],
        "backend": backend,
        "versions": {name: version(name) for name in ("pandas-ta-classic", "pandas", "numpy")},
        "dtype": spec.dtype,
        "kind": spec.kind,
        "validity": spec.validity,
        "missing_policy": spec.missing_policy,
        "readiness": "history-and-finite-v1",
        "unit": spec.unit,
        "engine_version": version("openbacktesting"),
        "inputs": {
            name: (source.metadata | {"channel": source.name})
            if isinstance(source, IndicatorHandle)
            else source
            for name, source in (inputs or {}).items()
        },
        "fixed": dict(spec.fixed),
    }
    key = json.dumps(metadata, sort_keys=True)

    def calculate():
        try:
            result = execute(spec, {name: data[name] for name in spec.inputs}, parameters, backend)
        except IndicatorError:
            raise
        except Exception as error:
            raise IndicatorError(
                "calculation-failed", indicator, str(error), backend=backend
            ) from error
        values, valid = to_arrays(spec, result, data.index, parameters)
        ready = np.arange(len(data)) >= spec.history_required(parameters) - 1
        current_valid = np.isfinite(data.to_numpy()).all(axis=1)
        valid &= ready
        if spec.validity == "current-inputs":
            valid &= current_valid
        # 未就绪数值不用于交易；保留 native 值便于诊断，不用填零伪装有效。
        if spec.dtype != "float64":
            values = np.nan_to_num(values).astype(spec.dtype)
        if len(spec.outputs) == 1:
            values, valid = values[0], valid[0]
        return IndicatorHandle(
            values,
            name=spec.outputs[0] if len(spec.outputs) == 1 else spec.outputs,
            index=data.index,
            valid=valid,
            metadata=metadata,
            ready=ready,
        )

    template = calculate() if cache is None else cache.get(key, calculate)
    handle = object.__new__(IndicatorHandle)
    handle.__dict__ = template.__dict__.copy()
    handle._metadata = deepcopy(template._metadata)
    handle._cursor = cursor or IndicatorCursor(len(frame), "complete")
    handle._set_required(spec.outputs.index(name) for name in required)
    handle._opts = template._opts.copy()
    handle._metadata["required_outputs"] = list(required)
    return handle


_OPTIMIZATION_CACHES = {}
_OPTIMIZATION_LOCK = RLock()


def optimization_cache(token, budget):
    """进程内复用；token 可序列化，缓存和锁不进入任务消息。"""
    with _OPTIMIZATION_LOCK:
        if token not in _OPTIMIZATION_CACHES:
            _OPTIMIZATION_CACHES[token] = IndicatorCache(budget)
        return _OPTIMIZATION_CACHES[token]


@contextmanager
def optimization_scope(budget):
    """父进程/线程在 finally 释放；子进程缓存随本次拥有的 Pool 退出释放。"""
    token = uuid4().hex
    optimization_cache(token, budget)
    try:
        yield token
    finally:
        with _OPTIMIZATION_LOCK:
            _OPTIMIZATION_CACHES.pop(token).clear()
