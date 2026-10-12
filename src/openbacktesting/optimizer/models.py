"""参数实验的纯值类型与规范编码。"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass


def encode(value) -> str:
    """规范 JSON；拒绝非有限数和非字符串键。"""

    def check(item):
        if isinstance(item, dict):
            if any(type(k) is not str for k in item):
                raise ValueError("optimizer: JSON 键必须为字符串")
            for child in item.values():
                check(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                check(child)

    check(value)
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def digest(value) -> str:
    return hashlib.sha256(encode(value).encode()).hexdigest()


@dataclass(frozen=True)
class Values:
    """有限候选值；由 plan 按对应 input 声明校验。"""

    values: tuple | list


@dataclass(frozen=True)
class Range:
    """升序格点范围；int 使用整数，float/price 使用十进制字符串或整数。"""

    start: int | str
    stop: int | str
    step: int | str


@dataclass(frozen=True)
class ExecutionIdentity:
    """宿主对已加载源码及本地依赖的 SHA256 声明，不加载或执行文件。"""

    strategy_sha256: str
    dependencies_sha256: str

    def __post_init__(self):
        for value in (self.strategy_sha256, self.dependencies_sha256):
            if not isinstance(value, str) or re.fullmatch("[0-9a-f]{64}", value) is None:
                raise ValueError("optimizer: 执行身份必须是小写 SHA256")


@dataclass(frozen=True)
class Plan:
    """不可变规范文本；snapshot 返回独立副本，组合在运行时逐项产生。"""

    _json: str

    def snapshot(self) -> dict:
        """返回完整计划的独立 JSON 副本。"""
        return json.loads(self._json)

    @property
    def total(self) -> int:
        """原始笛卡尔积数量，不扣除尚未检查的约束。"""
        return self.snapshot()["total"]


class OptimizationError(RuntimeError):
    """实验基础设施错误，保留结果位置、身份及最后已知提交数。"""

    def __init__(self, message, path, experiment_id, committed):
        self.path = str(path)
        self.experiment_id = experiment_id
        self.committed = committed
        super().__init__(
            f"{message}; path={path}; experiment={experiment_id}; committed={committed}"
        )


class _ExportError(ValueError):
    """单次回测已返回，但完整 Portfolio 导出失败。"""
