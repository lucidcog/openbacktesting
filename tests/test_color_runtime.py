"""Color parameters in actual runs, optimization, frozen results, and process transfer."""

import json
import multiprocessing as mp
import pickle
from multiprocessing.dummy import Pool as ThreadPool

import numpy as np
import pytest
from test_input_runtime import TradingInputs, compare
from test_inputs import request

import openbacktesting as api
from openbacktesting import Backtest, Color, colors, inputs
from openbacktesting.plotting import export_result
from openbacktesting.test import GOOG


class ColorInputs(TradingInputs):
    tint = inputs.color(colors.TEAL, title="Color")

    def init(self):
        super().init()
        assert type(self.tint) is Color
        self.soft = self.tint.with_transparency(50)
        self.plotting.line(self.close, color=self.tint)

    def next(self):
        super().next()
        self.plotting.bg_color(self.soft)
        self.plotting.bar_color(self.tint.with_transparency(100))
        if len(self.data) == 3:
            self.plotting.bg_color(None)


def test_run_color_binding_freeze_and_disabled():
    bt = Backtest(GOOG.iloc[:12], ColorInputs)
    results = [
        bt.run(tint="#22aa44"),
        bt.run(tint=Color(34, 170, 68)),
        bt.run_inputs(request(ColorInputs, {"Color": "#22aa44"})),
    ]
    for result in results:
        state = result["_strategy"]
        assert state.tint == Color(34, 170, 68)
        assert state.soft == Color(34, 170, 68, 128)
        assert pickle.loads(pickle.dumps(state)).tint == state.tint
        with pytest.raises(inputs.InputError, match="ImmutableInput"):
            state.tint = colors.RED
        assert result.attrs["input_snapshot"]["values"]["Color"] == "#22AA44FF"
        compare(results[0], result)
    payload = export_result(results[0])
    assert payload["plots"][0]["color"] == "#22AA44FF"
    assert {e["color"] for e in payload["colorEvents"]} == {"#22AA4480", "#22AA4400", None}
    json.dumps(payload, allow_nan=False)
    snapshot = results[0].attrs["input_snapshot"]
    compare(
        results[0],
        bt.run_inputs({k: snapshot[k] for k in ("schemaVersion", "schemaHash", "values")}),
    )
    results[0].pop("_strategy")
    results[0].attrs["plotting_result"] = pickle.loads(
        pickle.dumps(results[0].attrs["plotting_result"])
    )
    export_result(results[0])["colorEvents"].clear()
    assert export_result(results[0]) == payload
    disabled = Backtest(GOOG.iloc[:12], ColorInputs, plotting=False).run(tint="#22aa44")
    compare(results[1], disabled)
    assert "plotting_result" not in disabled.attrs
    assert disabled["_strategy"].plotting._color_events == []


@pytest.mark.parametrize("mode", ["thread", "spawn"])
def test_color_grid_and_best_rerun(monkeypatch, mode):
    factory = ThreadPool if mode == "thread" else mp.get_context("spawn").Pool
    monkeypatch.setattr(api, "Pool", lambda: factory(2))
    seen = []

    def constraint(p):
        assert type(p.tint) is Color
        seen.append(p.tint)
        return True

    bt = Backtest(GOOG.iloc[:12], ColorInputs)
    best, heatmap = bt.optimize(
        tint=["#22aa44", colors.RED, "#22AA44FF"],
        units=[1, 2],
        constraint=constraint,
        maximize="Return [%]",
        return_heatmap=True,
    )
    assert seen and len(heatmap) == 6  # Do not deduplicate equivalent candidate spellings.
    assert all(type(tint) is Color for tint in heatmap.index.get_level_values("tint"))
    selected = heatmap.idxmax()
    assert (np.asarray(heatmap.loc[selected]) == heatmap.max()).all()
    rerun = bt.run(**dict(zip(heatmap.index.names, selected)))
    compare(best, rerun)
    assert best.attrs["input_snapshot"]["values"]["Color"] == selected[0].to_hex()
    assert export_result(best) == export_result(rerun)
    assert pickle.loads(pickle.dumps(heatmap)).equals(heatmap)


def test_color_rejected_before_execution_or_candidate_filter(monkeypatch):
    bt = Backtest(GOOG.iloc[:12], ColorInputs)

    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid colors must not execute the strategy, constraint, or dispatch")

    monkeypatch.setattr(ColorInputs, "__init__", forbidden)
    monkeypatch.setattr(bt, "_broker", forbidden)
    monkeypatch.setattr(api, "Pool", forbidden)
    for value in [None, "red", {"red": 1}]:
        with pytest.raises(inputs.InputError, match="InvalidInputValue"):
            bt.run(tint=value)
        with pytest.raises(inputs.InputError, match="InvalidInputValue"):
            bt.optimize(tint=[colors.RED, value], constraint=forbidden, max_tries=0.01)
    with pytest.raises(inputs.InputError, match="InvalidInputValue"):
        bt.run_inputs(request(ColorInputs, {"Color": colors.RED}))
    with pytest.raises(inputs.InputError, match="UnsupportedOptimizationInput"):
        bt.optimize(tint=[colors.RED], method="sambo")
