"""A decorated author script verifies framework ownership without host, source-loader, or UI dependencies."""

import json
import runpy
from pathlib import Path
from types import MappingProxyType

import pandas as pd
import pytest
from example_support import example_chart
from test_backtest_declaration import chart
from test_backtest_declaration import namespace as module_namespace
from test_input_runtime import TradingInputs, compare

from openbacktesting import Backtest, Strategy, backtest, inputs, runtime
from openbacktesting.broker import InstrumentSpec
from openbacktesting.test import GOOG

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/strategies/ema_inputs.py"


def run(namespace, request=None):
    data = (
        example_chart(namespace)
        if isinstance(namespace, dict) and "__file__" in namespace
        else chart()
    )
    return runtime.run(namespace, request, **data)


def request(namespace, values):
    schema = runtime.describe(namespace)
    return {key: schema[key] for key in ("schemaVersion", "schemaHash")} | {"values": values}


def test_author_script_needs_only_declaration_and_discovery_does_not_run(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Discovery must not construct a strategy or run a backtest")

    # runpy loads trusted repository examples for tests only; runtime does not own source execution.
    with monkeypatch.context() as patch:
        patch.setattr(Strategy, "__init__", forbidden)
        patch.setattr(Backtest, "run", forbidden)
        namespace = runpy.run_path(str(EXAMPLE))
        schema = runtime.describe(namespace)
    assert "bt" not in namespace
    assert not {"schema", "request", "result", "runtime"} & namespace.keys()
    assert [item["title"] for item in schema["inputs"]] == [
        "Fast period",
        "Slow period",
        "Trade quantity",
        "Allow shorting",
    ]
    assert schema == json.loads(json.dumps(schema))
    # The framework does not require a separately exposed strategy class in namespace and also accepts read-only mappings.
    exported = MappingProxyType(namespace)
    assert runtime.describe(exported) == schema
    schema["inputs"][0]["default"] = 999
    assert runtime.describe(exported)["inputs"][0]["default"] == 12


def test_ema_title_injection_and_fresh_script_execution():
    first = runpy.run_path(str(EXAMPLE))
    config = json.loads(json.dumps(request(first, {"Fast period": 5, "Trade quantity": 2})))
    result = run(first, config)
    assert result["# Trades"] > 0
    assert result["_strategy"].fast == 5
    assert set(result["_trades"]["Size"]) == {2}
    assert result.attrs["input_snapshot"]["values"] == {
        "Fast period": 5,
        "Slow period": 26,
        "Trade quantity": 2,
        "Allow shorting": False,
    }
    second = runpy.run_path(str(EXAMPLE))
    assert runtime.discover(second) is not runtime.discover(first)
    assert "bt" not in second
    compare(result, run(second, config))
    defaults = run(second)
    assert defaults["_strategy"].fast == 12
    assert defaults.attrs["input_snapshot"]["overriddenTitles"] == []
    assert first["EmaCross"].fast.default == second["EmaCross"].fast.default == 12


@pytest.mark.parametrize("namespace", [None, [], {}, {"bt": None}, {"bt": Backtest}])
@pytest.mark.parametrize("operation", [runtime.describe, run])
def test_invalid_export_is_not_guessed(namespace, operation):
    with pytest.raises(TypeError, match="__name__|namespace"):
        operation(namespace)


def test_other_backtests_are_not_selected():
    bt = Backtest(GOOG.iloc[:12], TradingInputs)
    for operation in (runtime.describe, run):
        with pytest.raises(ValueError, match="backtest"):
            operation({"__name__": __name__, "bt": bt})


def test_reloaded_definition_rejects_saved_request_before_execution(monkeypatch):
    @backtest()
    class Original(TradingInputs):
        pass

    original = module_namespace(Original)
    config = request(original, {"Quantity": 2})

    @backtest()
    class Updated(TradingInputs):
        units = inputs.int(3, title="Quantity", minval=1)

    reloaded = module_namespace(Updated)
    assert runtime.describe(reloaded)["schemaHash"] != config["schemaHash"]

    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid inputs must not start the strategy")

    monkeypatch.setattr(Updated, "__init__", forbidden)
    with pytest.raises(inputs.InputError, match="SchemaMismatch"):
        run(reloaded, config)
    for invalid in ({}, False, request(reloaded, {"Quantity": "2"})):
        with pytest.raises(inputs.InputError):
            run(reloaded, invalid)


def test_legacy_strategy_has_empty_form_and_default_run():
    @backtest()
    class Legacy(Strategy):
        length = 20

        def init(self):
            self.observed = self.length

        def next(self):
            pass

    namespace = module_namespace(Legacy)
    assert runtime.describe(namespace)["inputs"] == []
    default = run(namespace, None)
    assert default["_strategy"].observed == 20
    assert "input_snapshot" not in default.attrs
    with pytest.raises(inputs.InputError):
        run(namespace, request(namespace, {}))


def test_subclass_instance_dispatch_preserves_fractional_units():
    class FractionalInputs(TradingInputs):
        def next(self):
            if len(self.data) == 2 and self.enabled:
                self.buy(qty=self.units / 10)
            elif len(self.data) == 5:
                self.close_position()

    class Observed(Backtest):
        def run(self, **kwargs):
            self.calls = getattr(self, "calls", 0) + 1
            return super().run(**kwargs)

    bt = Observed(GOOG.iloc[:12], FractionalInputs, instrument=InstrumentSpec(quantity_step=0.1))
    default = bt.run()
    schema = inputs.describe(FractionalInputs)
    titled = bt.run_inputs(
        {key: schema[key] for key in ("schemaVersion", "schemaHash")} | {"values": {"Quantity": 2}}
    )
    assert bt.calls == 2
    assert default["_trades"].Size.iloc[0] == 0.1
    assert titled["_trades"].Size.iloc[0] == 0.2
    pd.testing.assert_series_equal(titled["_trades"].EntryPrice, default["_trades"].EntryPrice)


def test_strategy_exception_propagates():
    namespace = runpy.run_path(str(EXAMPLE))
    with pytest.raises(ValueError, match="Fast period must be less than slow period"):
        run(namespace, request(namespace, {"Fast period": 30}))
    assert "bt" not in namespace


def test_plotting_author_export_is_frozen_and_has_real_visuals():
    from openbacktesting.plotting import export_result

    path = EXAMPLE.parent / "plotting.py"
    namespace = runpy.run_path(str(path))
    assert "bt" not in namespace
    runtime.describe(namespace)
    result = run(namespace)
    result.pop("_strategy")
    payload = export_result(result)
    assert len(payload["panes"]) == 2 and len(payload["plots"]) == 6
    assert {p["kind"] for p in payload["plots"]} == {"line", "step", "histogram", "level"}
    assert len(payload["fills"]) == 1
    signal = next(m for m in payload["markers"] if m["text"] == "Buy signal")
    assert signal["knownAtBar"] + 1 == payload["tradingFacts"]["fills"][0]["bar_index"]
    backdated = next(m for m in payload["markers"] if m["anchorBar"] != m["knownAtBar"])
    assert backdated["anchorBar"] == 57 and backdated["knownAtBar"] == 59
    assert all(
        s["kind"] == "numeric" and s["samplingMode"] == "offline" for s in payload["sources"]
    )
    assert all(p["color"] is None or isinstance(p["color"], str) for p in payload["plots"])
    assert json.loads(json.dumps(payload, allow_nan=False)) == payload
