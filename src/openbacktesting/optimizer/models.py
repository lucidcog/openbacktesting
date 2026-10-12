"""Plain-value types and canonical encoding for parameter experiments."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass


def encode(value) -> str:
    """Canonical JSON; reject nonfinite numbers and nonstring keys."""

    def check(item):
        if isinstance(item, dict):
            if any(type(k) is not str for k in item):
                raise ValueError("optimizer: JSON keys must be strings")
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
    """Finite candidate values; plan validates against the corresponding input declaration."""

    values: tuple | list


@dataclass(frozen=True)
class Range:
    """Ascending grid range; int uses integers, float/price uses decimal strings or integers."""

    start: int | str
    stop: int | str
    step: int | str


@dataclass(frozen=True)
class ExecutionIdentity:
    """Host declaration of SHA256 digests for loaded source and local dependencies; no files are loaded or executed."""

    strategy_sha256: str
    dependencies_sha256: str

    def __post_init__(self):
        for value in (self.strategy_sha256, self.dependencies_sha256):
            if not isinstance(value, str) or re.fullmatch("[0-9a-f]{64}", value) is None:
                raise ValueError("optimizer: execution identity must be a lowercase SHA256 digest")


@dataclass(frozen=True)
class Plan:
    """Immutable canonical text; snapshot returns an independent copy, and combinations are generated incrementally at runtime."""

    _json: str

    def snapshot(self) -> dict:
        """Return an independent JSON copy of the complete plan."""
        return json.loads(self._json)

    @property
    def total(self) -> int:
        """Raw Cartesian-product count, without deducting constraints not yet checked."""
        return self.snapshot()["total"]


class OptimizationError(RuntimeError):
    """Experiment infrastructure error preserving result location, identity, and last known committed count."""

    def __init__(self, message, path, experiment_id, committed):
        self.path = str(path)
        self.experiment_id = experiment_id
        self.committed = committed
        super().__init__(
            f"{message}; path={path}; experiment={experiment_id}; committed={committed}"
        )


class _ExportError(ValueError):
    """A backtest returned, but complete Portfolio export failed."""
