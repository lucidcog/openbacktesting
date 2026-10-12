"""每次运行独立的静态声明登记和运行标记；与交易执行解耦。"""

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
        "数值必须为实数，布尔值请显式转换",
    )
    return value


def _rgba(value):
    if value is None:
        return None
    try:
        return _as_color(value).to_hex()
    except (TypeError, ValueError) as error:
        raise PlottingError(
            "invalid-color", "颜色必须为 Color、#RRGGBB、#RRGGBBAA 或 None"
        ) from error


class Plotting:
    """通过 Strategy.plotting 访问；init 声明行情/指标图层，next/on_order/on_fill 添加标记。

    声明及标记的 id/title 可省略，title 默认使用最终 id；pane 默认主图。
    bg_color/bar_color 仅在 next 写入当根颜色，不创建身份、不跨 bar 继承。
    引用仅属于本次运行。纵轴自动适配，由消费者按可见有效数据计算范围。
    """

    def __init__(
        self,
        index: pd.Index,
        cursor: IndicatorCursor,
        *,
        enabled: bool = True,
        limits: PlottingLimits | None = None,
    ):
        _require(type(enabled) is bool, "invalid-option", "plotting 必须为 bool")
        _require(
            limits is None or isinstance(limits, PlottingLimits),
            "invalid-limit",
            "plotting_limits 必须为 PlottingLimits",
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
        _require(total <= getattr(self._limits, kind), "PlottingLimitExceeded", f"{kind} 超过预算")
        self._counts[kind] = total

    def _stage(self, *allowed):
        _require(self._phase in allowed, "invalid-phase", f"当前阶段 {self._phase} 不允许此操作")

    def _identity(self, cls, id, title):
        counter = cls.__name__
        if id is None:
            id = f"auto:{counter}:{self._counts[counter] + 1}"
        else:
            _require(
                isinstance(id, str) and bool(id) and not id.startswith("auto:") and id != "main",
                "invalid-id",
                "id 不得为空或占用 main/auto: 保留身份",
            )
        _require(id not in self._ids, "duplicate-id", id)
        title = id if title is None else title
        _require(isinstance(title, str), "invalid-title", "title 必须为文本")
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
            "引用类型或运行归属不匹配",
        )
        return ref.id

    def _pane(self, pane):
        return "main" if pane is None else self._ref(pane, PaneRef)

    def pane(self, id: str | None = None, title: str | None = None) -> PaneRef:
        """在 init 创建独立副图；返回引用供后续图层共享自动纵轴。"""
        self._stage("init")
        self._charge("panes", 1)
        ref = self._identity(PaneRef, id, title)
        self._panes.append({"id": ref.id, "title": ref.title, "axis": "bars", "scale": ref.id})
        return ref

    def _aligned(self, values, index):
        _require(
            isinstance(index, pd.Index) and index.equals(self._index),
            "misaligned-source",
            "index 必须与完整行情轴一致",
        )
        array = np.asarray(values)
        _require(array.shape == (self._n,), "invalid-source", "需要完整单通道序列")
        _require(
            array.dtype.kind in "iuf", "invalid-source", "需要实数数组，不接受 object/complex/bool"
        )
        return array

    def _source(self, values, valid, ready, unit, provenance):
        _require(unit is None or isinstance(unit, str), "invalid-unit", "unit 必须为文本或 None")
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
            "需要本运行单通道指标/行情句柄",
        )
        values = self._aligned(np.asarray(source), source._index())
        # 同底层、同通道的完整视图共享源；完整切片也不会复制多个载荷。
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
            gap_policy in ("break", "connect"), "invalid-style", "gap_policy 必须为 break/connect"
        )
        _require(
            type(offset_bars) is int and abs(offset_bars) <= 2**53 - 1,
            "invalid-offset",
            "offset_bars 必须为 JavaScript 安全整数",
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
        """声明线或阶梯线，默认主图、断开缺口；偏移只影响显示。"""
        _require(style in ("line", "step"), "invalid-style", "style 必须为 line/step")
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
        """声明柱图；有限 baseline 参与消费者自动纵轴范围计算。"""
        _require(np.isfinite(_number(baseline)), "invalid-value", "baseline 必须有限")
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
        """声明有限水平线，保存一个常量，不复制整条数组。"""
        _require(np.isfinite(_number(value)), "invalid-value", "level 必须有限")
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
        """填充两个图层之间的区域；端点必须具有相同面板、轴、偏移及兼容单位。"""
        self._stage("init")
        lo, hi = (self._plots[self._ref(r, PlotRef)] for r in (lower, upper))
        _require(
            all(lo[k] == hi[k] for k in ("pane", "axis", "scale", "offsetBars")),
            "incompatible-fill",
            "端点的面板/轴/偏移必须一致",
        )
        units = [self._sources[p["source"]]["unit"] for p in (lo, hi) if p["source"] is not None]
        _require(len(set(units)) <= 1, "incompatible-fill", "端点单位不兼容")
        _require(gap_policy in ("break", "connect"), "invalid-style", "未知缺口策略")
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
        _require(sequence <= 2**53 - 1, "PlottingLimitExceeded", "颜色序号超过安全整数")
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
        """仅在 next 为当前 bar 写入面板背景；同目标最后一次写入胜出。

        Args:
            color: 必填 Color、#RRGGBB、#RRGGBBAA 或 None；None 清除当根覆盖，透明色原样保留。
            pane: 默认主图，或本运行创建的副图引用。

        Raises:
            PlottingError: 阶段、颜色、面板归属非法，或超过共享事件预算。

        不跨 bar 继承；关闭采集仍校验并计数，不保留历史。
        """
        self._color("background", color, pane)

    def bar_color(self, color: Color | str | None) -> None:
        """仅在 next 为当前主图 K 线写色，统一表达实体、影线和边框覆盖。

        Args:
            color: 必填 Color、#RRGGBB、#RRGGBBAA 或 None；None 清除当根覆盖，透明色原样保留。

        Raises:
            PlottingError: 阶段或颜色非法，或超过共享事件预算。

        同 bar 最后一次写入胜出，不跨 bar 继承；不改变行情或自动纵轴。
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
        """记录运行标记；anchor_bar 可回标历史，knownAtBar 始终为当前 bar。"""
        self._stage("next", "on_order", "on_fill", "terminal_order", "terminal_fill")
        _require(
            position in ("above_bar", "below_bar", "price")
            and shape in ("circle", "square", "triangle_up", "triangle_down"),
            "invalid-style",
            "未知标记定位或形状",
        )
        if position == "price":
            _require(np.isfinite(_number(price)), "invalid-value", "price 定位需要有限价格")
            price = float(price)
        else:
            _require(price is None, "invalid-value", "只有 price 定位可指定价格")
        anchor = self._bar if anchor_bar is None else anchor_bar
        _require(
            type(anchor) is int and 0 <= anchor <= self._bar,
            "invalid-anchor",
            "anchor_bar 只能指向当前或过去的 bar",
        )
        _require(isinstance(text, str), "invalid-text", "text 必须为纯文本")
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
