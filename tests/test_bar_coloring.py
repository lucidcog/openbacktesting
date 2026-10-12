"""Per-bar colors: call semantics, budgets, lifecycle, and independent freezing."""

import json
import pickle

import numpy as np
import pandas as pd
import pytest
from test_engine_edges import Idle, flat_data
from test_plotting import VisualStrategy, handle

from openbacktesting import Backtest
from openbacktesting.indicators.types import IndicatorCursor
from openbacktesting.plotting import (
    PaneRef,
    Plotting,
    PlottingError,
    PlottingLimits,
    export_result,
)


def collector(enabled=True, **limits):
    p = Plotting(
        pd.RangeIndex(8), IndicatorCursor(8), enabled=enabled, limits=PlottingLimits(**limits)
    )
    p._enter("init")
    return p


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("method", ["bg_color", "bar_color"])
def test_color_validation_and_phase(enabled, method):
    p = collector(enabled)
    draw = getattr(p, method)
    for phase in (
        "closed",
        "init",
        "idle",
        "start",
        "finish",
        "on_order",
        "on_fill",
        "terminal_order",
        "terminal_fill",
    ):
        p._enter(phase)
        with pytest.raises(PlottingError, match="invalid-phase"):
            draw(None)
    p._enter("next", 1)
    for color in (
        "red",
        "#fffff",
        "#GG000000",
        0,
        True,
        [],
        np.array(["#ff0000ff"]),
        lambda: None,
        handle(p),
    ):
        with pytest.raises(PlottingError, match="invalid-color"):
            draw(color)
    with pytest.raises(TypeError):
        draw()
    for keyword in ("id", "title", "offset", "show_last", "force_overlay"):
        with pytest.raises(TypeError):
            draw(None, **{keyword: 1})
    assert draw("#00aaFF00") is None
    assert draw(None) is None
    assert p._counts["color"] == p._counts["events"] == 2
    assert len(p._color_events) == (2 if enabled else 0)
    p._close()
    assert p._color_events == []


@pytest.mark.parametrize("enabled", [True, False])
def test_color_reference_and_resource_boundaries(enabled):
    p = collector(enabled, events=3)
    pane = p.pane()
    other = collector().pane()
    source = handle(p)
    line = p.line(source)
    p._enter("next", 1)
    before = p._counts.copy()
    for invalid in ("main", other, PaneRef(pane.id, pane.title, p), source, line):
        with pytest.raises(PlottingError, match="invalid-reference"):
            p.bg_color(None, pane=invalid)
    assert p._counts == before
    with pytest.raises(TypeError):
        p.bar_color(None, pane=pane)
    p.marker()
    p.bg_color("#aaBBcc20", pane=pane)
    p.bar_color(None)
    with pytest.raises(PlottingError, match="events"):
        p.bar_color(None)
    assert p._counts["color"] == 2
    assert p._counts["points"] == before["points"]
    assert p._counts["plots"] == before["plots"]
    p._counts["color"] = 2**53 - 1
    with pytest.raises(PlottingError, match="safe-integer"):
        p.bar_color(None)


class Colors(Idle):
    fail = False

    def init(self):
        self.pane = self.plotting.pane(id="aux")

    def paint(self):
        self.plotting.bg_color("#ff000020")
        self.plotting.bg_color("#00ff0020", pane=self.pane)
        self.plotting.bar_color("#ff0000ff")
        self.plotting.bar_color("#00ff0000")
        self.plotting.bg_color(None)

    def next(self):
        if len(self.data) == 2:
            self.paint()
            if self.fail:
                raise RuntimeError("color failure")
        elif len(self.data) == 4:
            self.plotting.bar_color(None)


def merge(events, cutoff):
    state = {}
    for event in events:
        if event["knownAtBar"] > cutoff:
            continue
        key = (event["kind"], event["pane"], event["anchorBar"])
        if event["color"] is None:
            state.pop(key, None)
        else:
            state[key] = event["color"]
    return state


def test_frozen_colors_replay_and_run_isolation():
    bt = Backtest(flat_data(), Colors)
    r = bt.run()
    p = export_result(r)
    events = p["colorEvents"]
    assert p["schemaVersion"] == "1.1.0"
    assert p["requiredFeatures"] == ["core-v1", "bar-coloring-v1"]
    assert [e["sequence"] for e in events] == list(range(1, 7))
    assert [e["knownAtBar"] for e in events] == [1] * 5 + [3]
    assert all(
        e["anchorBar"] == e["knownAtBar"] and e["phase"] == "next" and e["axis"] == "bars"
        for e in events
    )
    assert merge(events, 0) == {}
    expected = {("background", "aux", 1): "#00FF0020", ("bar", "main", 1): "#00FF0000"}
    assert merge(events, 1) == expected
    assert merge(events, 7) == expected  # Without a call, colors do not carry across bars; null on another bar does not clear an earlier bar.
    assert merge(events[:1], 1) == {("background", "main", 1): "#FF000020"}
    assert r["_strategy"].plotting._color_events == []
    with pytest.raises(PlottingError, match="invalid-phase"):
        r["_strategy"].plotting.bar_color(None)
    r.pop("_strategy")
    saved = pd.Series(dtype=object)
    saved.attrs["plotting_result"] = pickle.loads(pickle.dumps(r.attrs["plotting_result"]))
    assert export_result(saved) == p
    json.dumps(saved.attrs, allow_nan=False)
    export_result(r)["colorEvents"].clear()
    assert export_result(r) == p
    with pytest.raises(RuntimeError, match="color failure"):
        bt.run(fail=True)
    assert export_result(r) == p
    assert export_result(bt.run()) == p


def test_snapshot_versions_and_empty_colors():
    r = Backtest(flat_data(), Idle).run()
    p = export_result(r)
    assert p["colorEvents"] == [] and p["requiredFeatures"] == ["core-v1"]
    snapshot = r.attrs["plotting_result"]
    p.pop("colorEvents")
    p["schemaVersion"] = "1.0.0"
    r.attrs["plotting_result"] = type(snapshot)("1.0.0", json.dumps(p), snapshot.byte_limit)
    assert export_result(r) == p
    r.attrs["plotting_result"] = type(snapshot)("1.1.0", json.dumps(p), snapshot.byte_limit)
    with pytest.raises(PlottingError, match="unsupported-version"):
        export_result(r)


@pytest.mark.parametrize("enabled", [True, False])
def test_total_event_budget_and_bytes(enabled):
    r = Backtest(flat_data(), Colors).run()
    p = export_result(r)
    count = len(p["colorEvents"]) + len(p["tradingFacts"]["account"])
    Backtest(
        flat_data(), Colors, plotting=enabled, plotting_limits=PlottingLimits(events=count)
    ).run()
    with pytest.raises(PlottingError, match="events"):
        Backtest(
            flat_data(), Colors, plotting=enabled, plotting_limits=PlottingLimits(events=count - 1)
        ).run()
    limited = Backtest(flat_data(), Colors, plotting_limits=PlottingLimits(bytes=1)).run()
    with pytest.raises(PlottingError, match="bytes"):
        export_result(limited)
    assert not limited["_account_curve"].empty


@pytest.mark.parametrize("method", ["bg_color", "bar_color"])
@pytest.mark.parametrize(
    "phase",
    ["init", "on_start", "on_finish", "on_order", "on_fill", "terminal_order", "terminal_fill"],
)
@pytest.mark.parametrize("enabled", [True, False])
def test_actual_forbidden_color_callbacks(method, phase, enabled):
    class Invalid(VisualStrategy):
        pass

    def illegal(self, *args):
        terminal = phase.startswith("terminal_")
        if not terminal or self.plotting._phase == phase:
            getattr(self.plotting, method)(None)

    callback = phase.replace("terminal_", "on_")
    setattr(Invalid, callback, illegal)
    with pytest.raises(PlottingError, match="invalid-phase"):
        Backtest(flat_data(), Invalid, plotting=enabled, end_policy="close_at_last_close").run()


def test_colors_every_bar_and_insolvency():
    class Warm(Idle):
        def init(self):
            self.signal = self.ind(lambda: np.array([np.nan, np.nan, 2, 3, np.nan, 5, 6, 7]))

        def next(self):
            self.plotting.bg_color("#abcdef80")

    p = export_result(Backtest(flat_data(), Warm).run())
    assert [e["anchorBar"] for e in p["colorEvents"]] == list(range(8))
    assert all(p["execution"]["strategyNext"][e["anchorBar"]] for e in p["colorEvents"])

    class Bankrupt(Idle):
        def next(self):
            self.plotting.bar_color(None)
            if len(self.data) == 2:
                self.buy(qty=20)

    data = flat_data()
    data.iloc[3:, :4] = 1
    p = export_result(Backtest(data, Bankrupt, cash=1000, margin=0.1).run())
    assert p["execution"]["endReason"] == "insolvent"
    assert [e["anchorBar"] for e in p["colorEvents"]] == [0, 1, 2]


@pytest.mark.parametrize("timing", ["next_open", "same_close"])
def test_coloring_preserves_calculations(timing):
    class Compare(VisualStrategy):
        draw = True

        def init(self):
            super().init()
            self.ema = self.ta.ema(length=2)

        def next(self):
            if self.draw:
                self.plotting.bg_color("#abcdef00")
            if len(self.data) == 3:
                self.buy(qty=1)
            super().next()

    runs = [
        Backtest(flat_data(), Compare, execution_timing=timing, plotting=enabled).run(
            draw=draw, colorize=draw
        )
        for enabled, draw in ((True, False), (True, True), (False, True))
    ]
    assert not runs[0]["_fills"].empty
    for r in runs[1:]:
        for key in ("_orders", "_fills", "_account_curve", "_trades", "_positions"):
            pd.testing.assert_frame_equal(r[key], runs[0][key])
        np.testing.assert_array_equal(r["_strategy"].ema, runs[0]["_strategy"].ema)
        np.testing.assert_array_equal(r["_strategy"].ema._gating, runs[0]["_strategy"].ema._gating)
        assert r["Equity Final [$]"] == runs[0]["Equity Final [$]"]
    assert export_result(runs[0])["market"] == export_result(runs[1])["market"]
    assert export_result(runs[0])["execution"] == export_result(runs[1])["execution"]
    assert "plotting_result" not in runs[2].attrs
