"""绘图声明、运行时序、隔离快照及非法输入的公开契约。"""

import json
import pickle
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest
from openbacktesting import Backtest, Strategy, backtest, inputs
from openbacktesting.indicators.types import IndicatorCursor, IndicatorHandle
from openbacktesting.plotting import (
    FillRef,
    MarkerRef,
    PaneRef,
    PlotRef,
    Plotting,
    PlottingError,
    PlottingLimits,
    export_result,
)
from openbacktesting.plotting.encoding import axis, scalar
from openbacktesting.runtime import describe
from test_engine_edges import Idle, flat_data


@pytest.fixture
def plotting():
    p = Plotting(pd.RangeIndex(8), IndicatorCursor(8))
    p._enter("init")
    return p


def handle(p, values=None, **kwargs):
    return IndicatorHandle(
        np.arange(8.0) if values is None else values,
        name="test",
        index=p._index,
        cursor=p._cursor,
        **kwargs,
    )


def test_references_defaults_and_shared_panes(plotting):
    p = plotting
    pane = p.pane()
    assert isinstance(pane, PaneRef) and pane.title == pane.id
    with pytest.raises(FrozenInstanceError):
        pane.id = "new"
    source = handle(p)
    lo = p.line(source, pane=pane, title="同名")
    hi = p.line(source, pane=pane, title="同名", style="step")
    assert isinstance(lo, PlotRef) and lo.title == hi.title
    fill = p.fill(lo, hi)
    assert isinstance(fill, FillRef)
    level = p.level(0, title="", pane=pane)
    assert level.title == "" and p._plots[level.id]["value"] == 0
    p.fill(level, hi)
    p.fill(level, level)
    default = p.line(source)
    assert p._plots[default.id]["pane"] == "main"
    assert not hasattr(p, "scale")


@pytest.mark.parametrize(
    "kwargs,code",
    [
        ({"id": ""}, "invalid-id"),
        ({"id": 2}, "invalid-id"),
        ({"id": "main"}, "invalid-id"),
        ({"id": "auto:x"}, "invalid-id"),
        ({"title": 3}, "invalid-title"),
    ],
)
def test_identity_validation(plotting, kwargs, code):
    with pytest.raises(PlottingError, match=code):
        plotting.pane(**kwargs)


def test_duplicates_domains_and_owner(plotting):
    p = plotting
    pane = p.pane(id="same")
    source = handle(p)
    with pytest.raises(PlottingError, match="duplicate-id"):
        p.pane(id="same")
    assert p._refs["same"] is pane
    for invalid in (
        "same",
        source,
        PaneRef(pane.id, pane.title, p),
        Plotting(pd.RangeIndex(8), IndicatorCursor(8)),
    ):
        with pytest.raises(PlottingError, match="invalid-reference"):
            p.line(source, pane=invalid)
    other = Plotting(pd.RangeIndex(8), IndicatorCursor(8))
    other._enter("init")
    with pytest.raises(PlottingError, match="invalid-reference"):
        p.line(source, pane=other.pane())
    with pytest.raises(PlottingError, match="invalid-source"):
        p.line(handle(other))


def test_sources_copy_masks_and_indicator_reuse(plotting):
    p = plotting
    original = np.array([0.0, np.nan, np.inf, -np.inf, 4, 5, 6, 7])
    valid = np.array([False, True, True, True, True, True, True, True])
    source = handle(p, original, valid=valid, metadata={"unit": "price"})
    source_id = p._plots[p.line(source).id]["source"]
    original[0] = 99
    valid[0] = True
    assert p._sources[source_id]["values"][0] == 0
    assert not p._sources[source_id]["valid"][0]
    h = handle(p, metadata={"unit": "price", "arbitrary": object(), "version": "1"})
    first, second = p.line(h), p.histogram(h)
    assert p._plots[first.id]["source"] == p._plots[second.id]["source"]
    assert len(p._sources) == 2
    p.line(h[:])
    multi = handle(p, np.vstack([np.arange(8.0), np.ones(8)]))
    with pytest.raises(PlottingError, match="invalid-source"):
        p.line(multi)
    p.line(multi[0])
    nonstring = handle(p)
    nonstring.name = ["one"]
    p.line(nonstring)
    for bad in (
        np.arange(8),
        handle(p)[1:],
        handle(p)[::-1],
        IndicatorHandle(np.ones(8), name="foreign", index=p._index),
    ):
        with pytest.raises(PlottingError):
            p.line(bad)


@pytest.mark.parametrize("values", [np.ones(7), np.ones((2, 8)), [True] * 8, [1j] * 8])
def test_invalid_indicator_plot_sources(plotting, values):
    with pytest.raises(PlottingError):
        plotting.line(handle(plotting, np.asarray(values)))


@pytest.mark.parametrize("method", ["line", "histogram"])
@pytest.mark.parametrize("values", [np.ones(8), [1.0] * 8, pd.Series(np.ones(8))])
def test_graphs_reject_raw_numeric_data(plotting, method, values):
    with pytest.raises(PlottingError, match="invalid-source"):
        getattr(plotting, method)(values)


def test_misaligned_indicator_and_invalid_unit(plotting):
    h = IndicatorHandle(
        np.ones(8), name="wrong", index=pd.RangeIndex(1, 9), cursor=plotting._cursor
    )
    with pytest.raises(PlottingError, match="misaligned-source"):
        plotting.line(h)
    with pytest.raises(PlottingError, match="invalid-unit"):
        plotting.line(handle(plotting, metadata={"unit": 4}))


@pytest.mark.parametrize(
    "method,args,kwargs",
    [
        ("line", (None,), {"style": "spline"}),
        ("line", (None,), {"gap_policy": "interpolate"}),
        ("line", (None,), {"offset_bars": True}),
        ("histogram", (None,), {"baseline": np.inf}),
        ("histogram", (None,), {"baseline": True}),
        ("level", (np.nan,), {}),
        ("level", (None,), {}),
        ("level", (1,), {"color": "red"}),
        ("level", (1,), {"color": lambda: None}),
    ],
)
def test_invalid_declaration_options(plotting, method, args, kwargs):
    with pytest.raises(PlottingError):
        getattr(plotting, method)(*args, **kwargs)


def test_fill_compatibility(plotting):
    p = plotting
    a = p.line(handle(p, metadata={"unit": "price"}))
    for b in (
        p.line(handle(p, metadata={"unit": "volume"})),
        p.level(2, pane=p.pane()),
        p.line(handle(p, metadata={"unit": "price"}), offset_bars=1),
    ):
        with pytest.raises(PlottingError, match="incompatible-fill"):
            p.fill(a, b)
    with pytest.raises(PlottingError, match="invalid-style"):
        p.fill(a, a, gap_policy="other")
    with pytest.raises(PlottingError, match="invalid-reference"):
        p.fill(a, "id")


def test_static_colors_and_removed_sampling_api(plotting):
    import openbacktesting.plotting as api
    from openbacktesting.plotting import types

    p = plotting
    source = handle(p)
    for name in ("source", "series", "color_source", "color_series"):
        assert not hasattr(p, name)
    for name in ("SourceRef", "SeriesRef", "ColorRef", "ColorSeriesRef"):
        assert not hasattr(api, name) and not hasattr(types, name)
    line = p.line(source, color="#00FF0080")
    assert p._plots[line.id]["color"] == "#00FF0080"
    assert p._plots[p.level(0).id]["color"] is None
    for color in (["#00ff00ff"] * 8, {"source": p._plots[line.id]["source"]}, source):
        for draw in (
            lambda color=color: p.line(source, color=color),
            lambda color=color: p.histogram(source, color=color),
            lambda color=color: p.level(0, color=color),
            lambda color=color: p.fill(line, line, color=color),
        ):
            with pytest.raises(PlottingError, match="invalid-color"):
                draw()
        p._enter("next", 1)
        with pytest.raises(PlottingError, match="invalid-color"):
            p.marker(color=color)
        p._enter("init")


@pytest.mark.parametrize("phase", ["closed", "init", "idle", "start", "finish"])
def test_runtime_phase_rejections(plotting, phase):
    plotting._enter(phase)
    with pytest.raises(PlottingError, match="invalid-phase"):
        plotting.marker()
    if phase != "init":
        with pytest.raises(PlottingError, match="invalid-phase"):
            plotting.pane()


def test_marker_timing_and_validation(plotting):
    p = plotting
    p._enter("next", 3)
    marker = p.marker(text="<script>plain text</script>", anchor_bar=1)
    assert isinstance(marker, MarkerRef)
    p.marker(position="price", price=0, shape="triangle_up")
    assert [(r["anchorBar"], r["knownAtBar"], r["sequence"]) for r in p._markers] == [
        (1, 3, 1),
        (3, 3, 2),
    ]
    for options in (
        {"anchor_bar": 4},
        {"anchor_bar": -1},
        {"anchor_bar": True},
        {"shape": "star"},
        {"position": "absolute"},
        {"position": "price"},
        {"position": "price", "price": np.inf},
        {"price": 1},
        {"text": 4},
        {"color": "red"},
    ):
        with pytest.raises(PlottingError):
            p.marker(**options)


class VisualStrategy(Strategy):
    colorize = True
    invalid_color = False
    failure = False
    style = "line"

    def init(self):
        self.plotting.line(self.close, style=self.style)
        self.plotting.histogram(self.volume, pane=self.plotting.pane(), color="#00ff00ff")

    def next(self):
        if self.colorize:
            self.plotting.bg_color("red" if self.invalid_color else "#ff000020")
            self.plotting.bar_color(None)
        if not self.plotting._enabled:
            assert self.plotting._color_events == []
        if self.failure:
            raise RuntimeError("strategy failure")
        if len(self.data) == 2:
            self.plotting.marker(text="signal")
            self.buy(qty=1)

    def on_fill(self, fill):
        self.plotting.marker(position="price", price=fill.price)

    def on_order(self, event):
        self.plotting.marker(text="order")


def test_frozen_run_trading_facts_and_error_isolation():
    bt = Backtest(flat_data(), VisualStrategy, end_policy="close_at_last_close")
    result = bt.run()
    payload = export_result(result)
    assert payload["execution"] == {
        "processed": [True] * 8,
        "strategyNext": [True] * 8,
        "endReason": "end_of_data",
        "lastProcessedBar": 7,
    }
    assert payload["markers"][0]["knownAtBar"] == 1
    assert payload["tradingFacts"]["fills"][0]["bar_index"] == 2
    assert [r["phase"] for r in payload["tradingFacts"]["account"]][-2:] == ["bar", "terminal"]
    assert {s["kind"] for s in payload["sources"]} == {"numeric"}
    assert {s["samplingMode"] for s in payload["sources"]} == {"offline"}
    assert {m["phase"] for m in payload["markers"]} >= {"terminal_order", "terminal_fill"}
    json.dumps(payload, allow_nan=False)
    json.dumps(result.attrs, allow_nan=False)
    with pytest.raises(TypeError):
        result.attrs["plotting_result"][0] = "bad"
    saved = pickle.loads(pickle.dumps(result))
    assert export_result(saved) == payload
    collector = result["_strategy"].plotting
    with pytest.raises(PlottingError, match="invalid-phase"):
        collector.marker()
    result.pop("_strategy")
    result["_fills"].loc[0, "price"] = 999
    exported = export_result(result)
    exported["markers"].clear()
    assert export_result(result) == payload
    with pytest.raises(RuntimeError, match="strategy failure"):
        bt.run(failure=True)
    assert export_result(result) == payload
    assert export_result(bt.run()) == payload


@pytest.mark.parametrize("timing,fill_bar", [("same_close", 1), ("next_open", 2)])
def test_styles_and_collection_do_not_change_trades(timing, fill_bar):
    results = [
        Backtest(flat_data(), VisualStrategy, plotting=enabled, execution_timing=timing).run(
            style=style
        )
        for enabled, style in ((True, "line"), (True, "step"), (False, "line"))
    ]
    for r in results[1:]:
        for key in ("_orders", "_fills", "_account_curve", "_trades", "_positions"):
            pd.testing.assert_frame_equal(results[0][key], r[key])
    assert export_result(results[0])["tradingFacts"]["fills"][0]["bar_index"] == fill_bar
    assert "plotting_result" not in results[-1].attrs
    with pytest.raises(PlottingError, match="missing-snapshot"):
        export_result(results[-1])


def test_disabled_identity_and_validation():
    ids = []
    for enabled in (True, False):
        p = Plotting(pd.RangeIndex(8), IndicatorCursor(8), enabled=enabled)
        p._enter("init")
        source = handle(p)
        line = p.line(source)
        source_id = p._plots[line.id]["source"]
        ids.append([source_id, line.id, p.pane().id])
        with pytest.raises(PlottingError, match="invalid-color"):
            p.line(source, color=["#00ff00ff"] * 8)
        p._enter("next", 2)
        ids[-1].append(p.marker().id)
        if not enabled:
            assert "values" not in p._sources[source_id]
            assert p._markers == [] and p._processed is None
    assert ids[0] == ids[1]


@pytest.mark.parametrize("name", ["panes", "plots", "points", "events", "text", "bytes"])
@pytest.mark.parametrize("value", [0, -1, True, 1.5, float("inf")])
def test_limits_config(name, value):
    with pytest.raises(PlottingError, match="invalid-limit"):
        PlottingLimits(**{name: value})


def test_limits_enforcement_and_export_errors():
    for enabled in (True, False):
        with pytest.raises(PlottingError, match="points"):
            Plotting(
                pd.RangeIndex(8),
                IndicatorCursor(8),
                enabled=enabled,
                limits=PlottingLimits(points=55),
            )
        p = Plotting(
            pd.RangeIndex(8),
            IndicatorCursor(8),
            enabled=enabled,
            limits=PlottingLimits(panes=1, plots=1, events=1, text=200),
        )
        p._enter("init")
        with pytest.raises(PlottingError, match="panes"):
            p.pane()
        p.level(0)
        with pytest.raises(PlottingError, match="plots"):
            p.level(0)
        with pytest.raises(PlottingError, match="text"):
            p.line(handle(p, metadata={"unit": "很长" * 100}))
        p._enter("next", 1)
        p.marker()
        with pytest.raises(PlottingError, match="events"):
            p.marker()
    result = Backtest(flat_data(), Idle, plotting_limits=PlottingLimits(bytes=1)).run()
    with pytest.raises(PlottingError, match="PlottingLimitExceeded"):
        export_result(result)
    assert result["_account_curve"].shape[0] > 0
    with pytest.raises(PlottingError, match="missing-snapshot"):
        export_result({})
    old = result.attrs["plotting_result"]
    result.attrs["plotting_result"] = type(old)("2.0.0", old.payload, old.byte_limit)
    with pytest.raises(PlottingError, match="unsupported-version"):
        export_result(result)
    for options in ({"enabled": 1}, {"limits": {}}):
        with pytest.raises(PlottingError):
            Plotting(pd.RangeIndex(8), IndicatorCursor(8), **options)
    for options in ({"plotting": 1}, {"plotting_limits": {}}):
        with pytest.raises(PlottingError):
            Backtest(flat_data(), Idle, **options)


def test_reserved_names_and_describe():
    for value in (1, lambda self: None, inputs.int(1, title="value")):
        cls = type("Collision", (Idle,), {"plotting": value})
        with pytest.raises((AttributeError, ValueError), match="plotting"):
            Backtest(flat_data(), cls).run()
    with pytest.raises(AttributeError, match="plotting"):
        Backtest(flat_data(), Idle).run(plotting=True)
    strategy = Backtest(flat_data(), Idle).run()["_strategy"]
    with pytest.raises(AttributeError, match="plotting"):
        strategy.plotting = None
    with pytest.raises(AttributeError, match="plotting"):
        del strategy.plotting

    @backtest()
    class Description(Idle):
        def init(self):
            raise AssertionError("init executed")

    # describe 接受已经加载的可信命名空间。
    assert describe({"__name__": __name__, "strategy": Description})["inputs"] == []


def test_strict_encoding_time_and_values():
    aware = pd.date_range("2025-01-01", periods=3, freq="ns", tz="Asia/Shanghai")
    assert axis(aware)["labels"] == [str(t.value) for t in aware]
    assert axis(aware)["timezone"] == "Asia/Shanghai"
    assert axis(aware.tz_localize(None))["kind"] == "naive-datetime"
    assert axis(pd.RangeIndex(3))["labels"] == ["0", "1", "2"]
    assert scalar(2**54) == str(2**54)
    assert scalar(np.bool_(True)) is True
    assert scalar(pd.Timestamp("2025-01-01")) == "2025-01-01T00:00:00"
    for v in (None, pd.NA, pd.NaT, np.nan, np.inf):
        assert scalar(v) is None
    with pytest.raises(PlottingError, match="invalid-value"):
        scalar(object())

    class Missing(Idle):
        def init(self):
            self.plotting.line(self.ind(lambda: np.array([0, np.nan, np.inf, 3, 4, 5, 6, 7])))

    payload = export_result(Backtest(flat_data(), Missing).run())
    source = payload["sources"][0]
    assert source["values"][:4] == [0, None, None, 3]
    assert source["missing"][:4] == [None, "non-finite", "non-finite", None]
    assert source["valid"] == [True, False, False, True, True, True, True, True]
    json.dumps(payload, allow_nan=False)


def test_actual_warmup_invalid_and_insolvent_masks():
    class Warm(Idle):
        def init(self):
            values = np.array([np.nan, np.nan, 2, 3, np.nan, 5, 6, 7])
            self.signal = self.ind(lambda: values)
            self.plotting.line(self.signal)

        def next(self):
            self.plotting.marker()

    p = export_result(Backtest(flat_data(), Warm).run())
    assert p["execution"]["strategyNext"] == [True] * 8

    class Never(Warm):
        def init(self):
            self.signal = self.ind(lambda: np.full(8, np.nan))

    p = export_result(Backtest(flat_data(), Never).run())
    assert p["execution"]["strategyNext"] == [True] * 8

    class Bankrupt(VisualStrategy):
        def next(self):
            self.plotting.marker()
            if len(self.data) == 2:
                self.buy(qty=20)

    data = flat_data()
    data.iloc[3:, :4] = 1
    result = Backtest(data, Bankrupt, cash=1000, margin=0.1).run()
    p = export_result(result)
    assert p["execution"]["endReason"] == "insolvent"
    assert p["execution"]["processed"] == [True] * 4 + [False] * 4
    assert p["execution"]["strategyNext"] == [True] * 3 + [False] * 5
    assert len(p["sources"][1]["values"]) == 8
    assert all(m["knownAtBar"] <= 3 for m in p["markers"])
    assert len(result["_strategy"].close) == 8


@pytest.mark.parametrize("phase", ["on_start", "on_finish"])
def test_real_forbidden_lifecycle(phase):
    class Phase(Idle):
        def init(self):
            self.plotting.line(self.close)

    setattr(Phase, phase, lambda s, *args: s.plotting.marker())
    with pytest.raises(PlottingError, match="invalid-phase"):
        Backtest(flat_data(), Phase).run()


def test_on_off_without_declarations_and_same_indicator_results():
    observed = []

    class Probe(Idle):
        draw = True

        def init(self):
            self.ema = self.ta.ema(length=2)
            if self.draw:
                self.plotting.line(self.ema)

        def next(self):
            observed.append(len(self.data))

    runs = []
    calls = []
    for enabled, draw in ((True, True), (False, True), (True, False)):
        observed.clear()
        runs.append(Backtest(flat_data(), Probe, plotting=enabled).run(draw=draw))
        calls.append(observed.copy())
    assert calls[0] == calls[1] == calls[2]
    for r in runs[1:]:
        np.testing.assert_array_equal(r["_strategy"].ema, runs[0]["_strategy"].ema)
        assert "warmup" not in r["_strategy"].ema._opts
        np.testing.assert_array_equal(r["_strategy"].ema.valid, runs[0]["_strategy"].ema.valid)
        assert r["_strategy"].ema._opts["index"].equals(runs[0]["_strategy"].ema._opts["index"])
        pd.testing.assert_frame_equal(r["_account_curve"], runs[0]["_account_curve"])
    empty = export_result(runs[-1])
    assert empty["plots"] == [] and empty["sources"] == [] and len(empty["panes"]) == 1


def test_grid_sambo_candidates_and_parallel_isolation(monkeypatch):
    from multiprocessing.pool import ThreadPool

    import openbacktesting

    monkeypatch.setattr(openbacktesting, "Pool", lambda: ThreadPool(2))
    scores = []

    def score(stats):
        assert "plotting_result" not in stats.attrs
        scores.append(stats["Equity Final [$]"])
        return stats["Equity Final [$]"]

    bt = Backtest(flat_data(), VisualStrategy, end_policy="close_at_last_close")
    best = bt.optimize(style=["line", "step"], maximize=score)
    assert len(scores) == 2 and export_result(best)["plots"]

    # SAMBO 支持普通原生参数；最优重跑恢复默认采集。
    class Native(VisualStrategy):
        amount = 1

    bt = Backtest(flat_data(), Native, end_policy="close_at_last_close")
    scores.clear()
    best = bt.optimize(
        amount=[1, 2, 3], method="sambo", max_tries=10, random_state=42, maximize=score
    )
    assert scores and export_result(best)["plots"]
    assert export_result(best)["colorEvents"]
    for method in ("grid", "sambo"):
        with pytest.raises(PlottingError, match="invalid-color"):
            bt.optimize(invalid_color=[True], method=method, max_tries=5, maximize=score)
        disabled = Backtest(flat_data(), Native, plotting=False, end_policy="close_at_last_close")
        result = disabled.optimize(amount=[1, 2], method=method, max_tries=5, maximize=score)
        assert "plotting_result" not in result.attrs
        assert result["_strategy"].plotting._color_events == []
    from openbacktesting.lib import MultiBacktest

    results = MultiBacktest([flat_data(), flat_data()], VisualStrategy).run()
    assert results.shape[1] == 2


def test_real_spawn_optimization():
    import subprocess
    import sys
    from pathlib import Path

    process = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plotting_spawn_probe.py"))],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert "spawn plotting isolated" in process.stdout
