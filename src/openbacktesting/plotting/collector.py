"""Independent static declaration registry and runtime markers per run, decoupled from trade execution."""

from __future__ import annotations

from collections import Counter
from importlib.metadata import version
from numbers import Real
from typing import Literal

import numpy as np
import pandas as pd

from openbacktesting.colors import Color, _as_color
from openbacktesting.indicators.types import IndicatorCursor, IndicatorHandle
from openbacktesting.plotting.encoding import axis, facts, freeze, numeric
from openbacktesting.plotting.types import (
    FillRef,
    MarkerRef,
    PaneRef,
    PlotRef,
    PlottingError,
    PlottingLimits,
)

Gap = Literal["break", "connect"]


def _require(condition, code, detail):
    if not condition:
        raise PlottingError(code, detail)


def _number(value):
    _require(
        isinstance(value, Real) and not isinstance(value, (bool, np.bool_)),
        "invalid-value",
        "Numeric values must be real; convert booleans explicitly",
    )
    return value


def _rgba(value):
    if value is None:
        return None
    try:
        return _as_color(value).to_hex()
    except (TypeError, ValueError) as error:
        raise PlottingError(
            "invalid-color", "Color must be Color, #RRGGBB, #RRGGBBAA, or None"
        ) from error


class Plotting:
    """Access through Strategy.plotting; init declares market-data/indicator layers, and next/on_order/on_fill add markers.

    Declaration and marker id/title are optional; title defaults to the final id, and pane defaults to the main chart.
    bg_color/bar_color write current-bar colors only in next, without creating identities or inheriting across bars.
    References belong only to this run. Consumers autoscale the vertical axis using visible valid data.
    """

    def __init__(
        self,
        index: pd.Index,
        cursor: IndicatorCursor,
        *,
        enabled: bool = True,
        limits: PlottingLimits | None = None,
    ):
        _require(type(enabled) is bool, "invalid-option", "plotting must be bool")
        _require(
            limits is None or isinstance(limits, PlottingLimits),
            "invalid-limit",
            "plotting_limits must be PlottingLimits",
        )
        self._enabled = enabled
        self._limits = limits or PlottingLimits()
        self._index = index.copy(deep=True)
        self._cursor = cursor
        self._n = len(index)
        self._phase = "closed"
        self._bar = -1
        self._counts = Counter()
        self._ids = {"main"}
        self._refs = {}
        self._sources = {}
        self._dedupe = {}
        self._panes = [{"id": "main", "title": "main", "axis": "bars", "scale": "main"}]
        self._plots = {}
        self._fills = []
        self._markers = []
        self._color_events = []
        self._charge("panes", 1)
        self._charge("points", self._n * 7)
        self._processed = np.zeros(self._n, bool) if enabled else None
        self._next = np.zeros(self._n, bool) if enabled else None

    def _charge(self, kind, count):
        total = self._counts[kind] + count
        _require(total <= getattr(self._limits, kind), "PlottingLimitExceeded", f"{kind} exceeds the budget")
        self._counts[kind] = total

    def _stage(self, *allowed):
        _require(self._phase in allowed, "invalid-phase", f"Current phase {self._phase} does not allow this operation")

    def _identity(self, cls, id, title):
        counter = cls.__name__
        if id is None:
            id = f"auto:{counter}:{self._counts[counter] + 1}"
        else:
            _require(
                isinstance(id, str) and bool(id) and not id.startswith("auto:") and id != "main",
                "invalid-id",
                "id must not be empty or use reserved main/auto: identities",
            )
        _require(id not in self._ids, "duplicate-id", id)
        title = id if title is None else title
        _require(isinstance(title, str), "invalid-title", "title must be text")
        self._charge("text", len((id + title).encode()))
        self._counts[counter] += 1
        self._ids.add(id)
        ref = cls(id, title, self)
        self._refs[id] = ref
        return ref

    def _ref(self, ref, cls):
        _require(
            isinstance(ref, cls) and ref._owner is self and self._refs.get(ref.id) is ref,
            "invalid-reference",
            "Reference type or owning run does not match",
        )
        return ref.id

    def _pane(self, pane):
        return "main" if pane is None else self._ref(pane, PaneRef)

    def pane(self, id: str | None = None, title: str | None = None) -> PaneRef:
        """Create a separate pane in init; return a reference for subsequent layers to share an automatically scaled vertical axis."""
        self._stage("init")
        self._charge("panes", 1)
        ref = self._identity(PaneRef, id, title)
        self._panes.append({"id": ref.id, "title": ref.title, "axis": "bars", "scale": ref.id})
        return ref

    def _aligned(self, values, index):
        _require(
            isinstance(index, pd.Index) and index.equals(self._index),
            "misaligned-source",
            "index must match the complete market-data axis",
        )
        array = np.asarray(values)
        _require(array.shape == (self._n,), "invalid-source", "A complete single-channel sequence is required")
        _require(
            array.dtype.kind in "iuf", "invalid-source", "A real-valued array is required; object/complex/bool are not accepted"
        )
        return array

    def _source(self, values, valid, ready, unit, provenance):
        _require(unit is None or isinstance(unit, str), "invalid-unit", "unit must be text or None")
        self._charge("points", self._n)
        self._charge("text", len((unit or "").encode()))
        id = f"auto:source:{len(self._sources) + 1}"
        self._charge("text", len(id.encode()) * 2)
        row = {
            "id": id,
            "title": id,
            "axis": "bars",
            "unit": unit,
            "samplingMode": "offline",
            "kind": "numeric",
            "provenance": provenance or {},
        }
        if self._enabled:
            row.update(values=values.copy(), valid=valid.copy(), ready=ready.copy())
        self._sources[id] = row
        return id

    def _adapt(self, source):
        _require(
            isinstance(source, IndicatorHandle) and source._cursor is self._cursor,
            "invalid-source",
            "A single-channel indicator/market-data handle from this run is required",
        )
        values = self._aligned(np.asarray(source), source._index())
        # Complete views of the same buffer and channel share a source; full slices do not duplicate payloads.
        key = (id(source._values), repr(source._selectors))
        if key not in self._dedupe:
            meta = source.metadata
            provenance = {
                k: v
                for k, v in meta.items()
                if k in {"id", "version", "backend", "unit", "kind", "field"} and isinstance(v, str)
            }
            if isinstance(source.name, str):
                provenance["channel"] = source.name
            source_id = self._source(
                values,
                source.valid,
                source.ready,
                meta.get("unit"),
                provenance,
            )
            self._dedupe[key] = source_id
        return self._dedupe[key]

    def _plot(self, kind, source, id, title, pane, color, gap_policy, offset_bars, **extra):
        self._stage("init")
        _require(
            gap_policy in ("break", "connect"), "invalid-style", "gap_policy must be break/connect"
        )
        _require(
            type(offset_bars) is int and abs(offset_bars) <= 2**53 - 1,
            "invalid-offset",
            "offset_bars must be a JavaScript safe integer",
        )
        target = self._pane(pane)
        paint = _rgba(color)
        source_id = None if kind == "level" else self._adapt(source)
        self._charge("plots", 1)
        ref = self._identity(PlotRef, id, title)
        self._plots[ref.id] = {
            "id": ref.id,
            "title": ref.title,
            "kind": kind,
            "pane": target,
            "axis": "bars",
            "scale": target,
            "source": source_id,
            "color": paint,
            "gapPolicy": gap_policy,
            "offsetBars": offset_bars,
            **extra,
        }
        return ref

    def line(
        self,
        source: IndicatorHandle,
        id: str | None = None,
        title: str | None = None,
        pane: PaneRef | None = None,
        color: Color | str | None = None,
        style: Literal["line", "step"] = "line",
        gap_policy: Gap = "break",
        offset_bars: int = 0,
    ) -> PlotRef:
        """Declare a line or step line, defaulting to the main chart with broken gaps; offsets affect display only."""
        _require(style in ("line", "step"), "invalid-style", "style must be line/step")
        return self._plot(style, source, id, title, pane, color, gap_policy, offset_bars)

    def histogram(
        self,
        source: IndicatorHandle,
        id: str | None = None,
        title: str | None = None,
        pane: PaneRef | None = None,
        color: Color | str | None = None,
        baseline: float = 0,
        gap_policy: Gap = "break",
        offset_bars: int = 0,
    ) -> PlotRef:
        """Declare a histogram; a finite baseline contributes to consumer vertical-axis autoscaling."""
        _require(np.isfinite(_number(baseline)), "invalid-value", "baseline must be finite")
        return self._plot(
            "histogram",
            source,
            id,
            title,
            pane,
            color,
            gap_policy,
            offset_bars,
            baseline=float(baseline),
        )

    def level(
        self,
        value: float,
        id: str | None = None,
        title: str | None = None,
        pane: PaneRef | None = None,
        color: Color | str | None = None,
    ) -> PlotRef:
        """Declare a finite horizontal line, storing one constant rather than duplicating a full array."""
        _require(np.isfinite(_number(value)), "invalid-value", "level must be finite")
        return self._plot("level", None, id, title, pane, color, "break", 0, value=float(value))

    def fill(
        self,
        lower: PlotRef,
        upper: PlotRef,
        id: str | None = None,
        title: str | None = None,
        color: Color | str | None = None,
        gap_policy: Gap = "break",
    ) -> FillRef:
        """Fill between two layers; endpoints must share pane, axis, offset, and compatible units."""
        self._stage("init")
        lo, hi = (self._plots[self._ref(r, PlotRef)] for r in (lower, upper))
        _require(
            all(lo[k] == hi[k] for k in ("pane", "axis", "scale", "offsetBars")),
            "incompatible-fill",
            "Endpoint panes/axes/offsets must match",
        )
        units = [self._sources[p["source"]]["unit"] for p in (lo, hi) if p["source"] is not None]
        _require(len(set(units)) <= 1, "incompatible-fill", "Endpoint units are incompatible")
        _require(gap_policy in ("break", "connect"), "invalid-style", "Unknown gap policy")
        paint = _rgba(color)
        self._charge("plots", 1)
        ref = self._identity(FillRef, id, title)
        self._fills.append(
            {
                "id": ref.id,
                "title": ref.title,
                "lower": lo["id"],
                "upper": hi["id"],
                "pane": lo["pane"],
                "axis": "bars",
                "scale": lo["scale"],
                "color": paint,
                "gapPolicy": gap_policy,
            }
        )
        return ref

    def _color(self, kind, color, pane):
        self._stage("next")
        target, paint = self._pane(pane), _rgba(color)
        sequence = self._counts["color"] + 1
        _require(sequence <= 2**53 - 1, "PlottingLimitExceeded", "Color index exceeds the safe-integer range")
        self._charge("events", 1)
        self._counts["color"] = sequence
        if self._enabled:
            self._color_events.append(
                {
                    "kind": kind,
                    "pane": target,
                    "axis": "bars",
                    "anchorBar": self._bar,
                    "knownAtBar": self._bar,
                    "phase": "next",
                    "sequence": sequence,
                    "color": paint,
                }
            )

    def bg_color(self, color: Color | str | None, *, pane: PaneRef | None = None) -> None:
        """Write the current bar's pane background only in next; the last write to the same target wins.

        Args:
            color: Required Color, #RRGGBB, #RRGGBBAA, or None; None clears the current-bar override, while transparent colors are preserved.
            pane: Main chart by default, or a separate-pane reference created in this run.

        Raises:
            PlottingError: Invalid phase, color, or pane ownership, or shared event budget exceeded.

        No cross-bar inheritance; disabled collection still validates and counts without retaining history.
        """
        self._color("background", color, pane)

    def bar_color(self, color: Color | str | None) -> None:
        """Color the current main-chart candle only in next, applying one override to body, wick, and border.

        Args:
            color: Required Color, #RRGGBB, #RRGGBBAA, or None; None clears the current-bar override, while transparent colors are preserved.

        Raises:
            PlottingError: Invalid phase or color, or shared event budget exceeded.

        The last write on a bar wins, without cross-bar inheritance; market data and automatic vertical axes remain unchanged.
        """
        self._color("bar", color, None)

    def marker(
        self,
        id: str | None = None,
        title: str | None = None,
        pane: PaneRef | None = None,
        *,
        position: Literal["above_bar", "below_bar", "price"] = "above_bar",
        price: float | None = None,
        shape: Literal["circle", "square", "triangle_up", "triangle_down"] = "circle",
        text: str = "",
        color: Color | str | None = None,
        anchor_bar: int | None = None,
    ) -> MarkerRef:
        """Record a runtime marker; anchor_bar may refer to historical bars, while knownAtBar is always the current bar."""
        self._stage("next", "on_order", "on_fill", "terminal_order", "terminal_fill")
        _require(
            position in ("above_bar", "below_bar", "price")
            and shape in ("circle", "square", "triangle_up", "triangle_down"),
            "invalid-style",
            "Unknown marker location or shape",
        )
        if position == "price":
            _require(np.isfinite(_number(price)), "invalid-value", "price location requires a finite price")
            price = float(price)
        else:
            _require(price is None, "invalid-value", "Only price location allows a price")
        anchor = self._bar if anchor_bar is None else anchor_bar
        _require(
            type(anchor) is int and 0 <= anchor <= self._bar,
            "invalid-anchor",
            "anchor_bar may refer only to the current or a past bar",
        )
        _require(isinstance(text, str), "invalid-text", "text must be plain text")
        target, paint = self._pane(pane), _rgba(color)
        self._charge("events", 1)
        self._charge("text", len(text.encode()))
        ref = self._identity(MarkerRef, id, title)
        if self._enabled:
            self._markers.append(
                {
                    "id": ref.id,
                    "title": ref.title,
                    "pane": target,
                    "axis": "bars",
                    "scale": target,
                    "anchorBar": anchor,
                    "knownAtBar": self._bar,
                    "phase": self._phase,
                    "sequence": self._counts["MarkerRef"],
                    "position": position,
                    "price": price,
                    "shape": shape,
                    "text": text,
                    "color": paint,
                }
            )
        return ref

    def _enter(self, phase, bar=None):
        self._phase = phase
        if bar is not None:
            self._bar = bar
            if self._enabled:
                self._processed[bar] = True
                if phase == "next":
                    self._next[bar] = True

    def _finish(self, result, market, reason):
        self._phase = "closed"
        self._charge("events", len(result["_fills"]) + len(result["_account_curve"]))
        if not self._enabled:
            return None
        sources = []
        for row in self._sources.values():
            item = {k: v for k, v in row.items() if k not in {"values", "valid", "ready"}}
            item.update(numeric(row["values"], row["valid"], row["ready"]))
            sources.append(item)
        columns = [
            "fill_id",
            "order_id",
            "bar_index",
            "phase",
            "sequence",
            "side",
            "qty",
            "price",
            "fee",
        ]
        account_columns = [c for c in result["_account_curve"].columns if c != "timestamp"]
        payload = {
            "schemaVersion": "1.1.0",
            "engineVersion": version("openbacktesting"),
            "axes": [axis(self._index)],
            "panes": self._panes,
            "scales": [
                {"id": p["scale"], "pane": p["id"], "mode": "auto", "rangePolicy": "visible-valid"}
                for p in self._panes
            ],
            "sources": sources,
            "plots": list(self._plots.values()),
            "fills": self._fills,
            "markers": self._markers,
            "colorEvents": self._color_events,
            "market": {
                "axis": "bars",
                **{
                    c.lower(): numeric(
                        market[c].to_numpy(),
                        np.isfinite(market[c].to_numpy()),
                        np.ones(self._n, bool),
                    )
                    for c in ("Open", "High", "Low", "Close", "Volume")
                },
            },
            "tradingFacts": {
                "fills": facts(result["_fills"], columns),
                "account": facts(result["_account_curve"], account_columns),
            },
            "execution": {
                "processed": self._processed.tolist(),
                "strategyNext": self._next.tolist(),
                "endReason": reason,
                "lastProcessedBar": self._bar,
            },
            "requiredFeatures": ["core-v1"] + (["bar-coloring-v1"] if self._color_events else []),
            "optionalFeatures": [],
            "diagnostics": [],
        }
        return freeze(payload, self._limits.bytes)

    def _close(self):
        self._phase = "closed"
        self._sources.clear()
        self._dedupe.clear()
        self._markers.clear()
        self._color_events.clear()
        self._processed = self._next = None
