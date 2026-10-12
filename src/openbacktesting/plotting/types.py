"""Immutable plotting-declaration identities, budgets, and stable errors without rendering capabilities."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any


class PlottingError(ValueError):
    """Plotting contract error; code is a stable category for caller dispatch."""

    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class PlottingLimits:
    """Collection budgets; all limits are positive integers, and bytes is checked during explicit export.

    points counts unique dense sources, including five market-data columns and two execution masks.
    panes includes the main chart; plots includes fills; events includes every color call, marker, and trade fact.
    text is the cumulative UTF-8 byte count of author identities, titles, units, and marker text.
    """

    panes: int = 32
    plots: int = 256
    points: int = 10_000_000
    events: int = 1_000_000
    text: int = 1_048_576
    bytes: int = 268_435_456

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value <= 0:
                raise PlottingError("invalid-limit", f"{field.name} must be a positive integer")


@dataclass(frozen=True)
class _Ref:
    id: str
    title: str
    _owner: Any


@dataclass(frozen=True)
class PaneRef(_Ref):
    """Separate-pane identity for the current run; pass this reference only to pane arguments."""


@dataclass(frozen=True)
class PlotRef(_Ref):
    """Line, histogram, or horizontal-line identity usable as a fill endpoint."""


@dataclass(frozen=True)
class FillRef(_Ref):
    """Fill identity between two compatible layers."""


@dataclass(frozen=True)
class MarkerRef(_Ref):
    """Identity of one runtime marker."""


class _Snapshot(tuple):
    """Immutable plain-value tuple; the entire result.attrs remains JSON-encodable."""

    __slots__ = ()

    def __new__(cls, version: str, payload: str, byte_limit: int):
        return super().__new__(cls, (version, payload, byte_limit, len(payload.encode())))

    def __getnewargs__(self):
        return self[:3]

    @property
    def version(self):
        return self[0]

    @property
    def payload(self):
        return self[1]

    @property
    def byte_limit(self):
        return self[2]

    @property
    def byte_length(self):
        return self[3]
