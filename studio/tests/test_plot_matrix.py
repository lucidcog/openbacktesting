"""Core-to-Studio drawing matrix; regenerate the browser fixture by running this file."""

import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from openbacktesting import Backtest, Strategy, backtest
from openbacktesting.plotting import Plotting, export_result
from openbacktesting.portfolio import export_result as export_portfolio

from openbacktesting_studio.artifacts import import_portfolio
from openbacktesting_studio.host.projection import project

PANES = ("main", "secondary")
KINDS = ("line", "step", "histogram", "level")
SHAPES = ("circle", "square", "triangle_up", "triangle_down")
POSITIONS = ("above_bar", "below_bar", "price")
FIXTURE = Path(__file__).parent / "fixtures" / "plotting-matrix.json"


@backtest()
class DrawingMatrix(Strategy):
    def init(self):
        self.secondary = self.plotting.pane(id="secondary", title="Drawing matrix")
        for name, pane in (("main", None), ("secondary", self.secondary)):
            lower = self.plotting.line(
                self.close, id=f"{name}-line", title=f"{name} line", pane=pane, color="#2962ff"
            )
            self.plotting.line(
                self.open,
                id=f"{name}-step",
                title=f"{name} step",
                pane=pane,
                style="step",
                color="#ff9800",
            )
            self.plotting.histogram(
                self.low,
                id=f"{name}-histogram",
                title=f"{name} histogram",
                pane=pane,
                baseline=95,
                color="#26a69a50",
            )
            upper = self.plotting.level(
                108, id=f"{name}-level", title=f"{name} level", pane=pane, color="#ab47bc"
            )
            self.plotting.fill(lower, upper, id=f"{name}-fill", color="#2962ff20")

    def next(self):
        bar = len(self.data) - 1
        if bar == 2:
            self.plotting.bar_color("#ffaa00")
        if bar == 3:
            self.plotting.bar_color("#ffaa00")
            self.plotting.bar_color(None)
        for name, pane in (("main", None), ("secondary", self.secondary)):
            self.plotting.bg_color("#26a69a10", pane=pane)
            if bar == 3:
                self.plotting.bg_color(None, pane=pane)
            for index, (shape, position) in enumerate(
                (shape, position) for shape in SHAPES for position in POSITIONS
            ):
                if bar == index + 2:
                    self.plotting.marker(
                        id=f"{name}-{shape}-{position}",
                        pane=pane,
                        shape=shape,
                        position=position,
                        price=103 if position == "price" else None,
                        text=f"{shape} {position}",
                        color="#ef5350",
                    )


def make_result():
    close = 100 + np.sin(np.arange(32) * 0.4) * 3
    data = pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": np.arange(32) + 100,
        },
        index=pd.date_range("2024-01-01", periods=32),
    )
    return Backtest(data, DrawingMatrix).run()


def make_payload():
    return export_result(make_result())


@pytest.fixture(scope="module")
def payload():
    return make_payload()


def test_browser_fixture_matches_real_core_export(payload):
    assert json.loads(FIXTURE.read_text()) == payload


@pytest.mark.parametrize("pane", PANES)
@pytest.mark.parametrize("kind", KINDS)
def test_every_plot_exports_and_projects_into_its_pane(payload, pane, kind):
    plot = next(plot for plot in payload["plots"] if plot["id"] == f"{pane}-{kind}")
    assert (plot["kind"], plot["pane"], plot["scale"]) == (kind, pane, pane)
    projected = project(payload, 2, 20, 100)["plotting"]
    assert next(item for item in projected["plots"] if item["id"] == plot["id"]) == plot
    if kind == "level":
        assert plot["value"] == 108
    else:
        source = next(item for item in payload["sources"] if item["id"] == plot["source"])
        result = next(item for item in projected["sources"] if item["id"] == plot["source"])
        assert result["values"] == source["values"][2:20]


@pytest.mark.parametrize("pane", PANES)
def test_fill_and_background_retain_pane_and_clear_events(payload, pane):
    fill = next(fill for fill in payload["fills"] if fill["pane"] == pane)
    assert (fill["lower"], fill["upper"], fill["scale"]) == (
        f"{pane}-line",
        f"{pane}-level",
        pane,
    )
    projected = project(payload, 2, 20, 100)["plotting"]
    assert fill in projected["fills"]
    events = [
        event
        for event in projected["colorEvents"]
        if event["pane"] == pane and event["kind"] == "background"
    ]
    assert events and events[0]["anchorBar"] == 2
    assert [event for event in events if event["anchorBar"] == 3][-1]["color"] is None


@pytest.mark.parametrize("pane", PANES)
@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize("position", POSITIONS)
def test_each_marker_shape_and_position_in_both_panes(payload, pane, shape, position):
    marker = next(item for item in payload["markers"] if item["id"] == f"{pane}-{shape}-{position}")
    assert (marker["pane"], marker["scale"], marker["shape"], marker["position"]) == (
        pane,
        pane,
        shape,
        position,
    )
    assert marker["price"] == (103 if position == "price" else None)
    assert marker in project(payload, 2, 20, 100)["plotting"]["markers"]


def test_candle_color_is_main_only_by_public_contract(payload):
    assert "pane" not in inspect.signature(Plotting.bar_color).parameters
    events = [event for event in payload["colorEvents"] if event["kind"] == "bar"]
    assert events and {event["pane"] for event in events} == {"main"}
    assert events[-1]["color"] is None


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(make_payload(), indent=2, allow_nan=False) + "\n")


@pytest.mark.parametrize("mismatch", [False, True])
def test_real_paired_export_accepts_naive_dates_but_rejects_changed_bars(tmp_path, mismatch):
    result = make_result()
    plotting = export_result(result)
    if mismatch:
        plotting["axes"][0]["labels"][2] = "2024-01-03T00:00:00.000000001"
    paired = {"portfolio": export_portfolio(result), "plotting": plotting}
    source = tmp_path / "paired.json"
    source.write_text(json.dumps(paired))
    target = tmp_path / "imported"
    if mismatch:
        with pytest.raises(ValueError, match="bar identities"):
            import_portfolio(source, target)
        assert not target.exists()
    else:
        import_portfolio(source, target)
        assert json.loads((target / "plotting.json").read_text()) == plotting
