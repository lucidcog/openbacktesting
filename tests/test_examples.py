"""Example selection index, loading boundaries, and real execution; explicit execution sets provide semantic coverage."""

import ast
import builtins
import io
import os
import re
import runpy
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path
from urllib.parse import unquote

import numpy as np
import pandas as pd
import pytest
from example_support import example_chart

from openbacktesting import Backtest, Color, Strategy, runtime
from openbacktesting.indicators import compute
from openbacktesting.indicators.methods import TechnicalAnalysis
from openbacktesting.plotting import export_result
from openbacktesting.test import GOOG

ENGINE = Path(__file__).resolve().parents[1]
EXAMPLES = ENGINE / "examples"
# Test each entry point explicitly rather than treating an unknown new example's successful load as execution.
# New topics must extend the execution set/assertions; there is no fixed example-count limit.
AUTHORS = (
    "strategies/local_value_helpers.py",
    "strategies/local_builtin_indicators.py",
    "strategies/closed_trade_statistics.py",
    "strategies/strategy_logs.py",
    "strategies/bar_states.py",
    "strategies/custom_indicators.py",
    "strategies/plotting.py",
    "strategies/trading_lifecycle.py",
    "strategies/fractional_sizing.py",
    "strategies/managed_orders.py",
    "strategies/first_backtest.py",
    "strategies/ema_macd.py",
    "strategies/data_sources.py",
    "strategies/confirmed_events.py",
    "strategies/cross_signals.py",
    "strategies/ema_inputs.py",
    "strategies/all_inputs.py",
)
TUTORIALS = (
    "advanced/optimizer_results.py",
    "advanced/portfolio_report.py",
    "advanced/strategy_logs.py",
    "advanced/chart_context.py",
    "advanced/strategy_settings.py",
    "advanced/plotting_export.py",
    "advanced/run_author.py",
    "advanced/indicator_reference.py",
    "advanced/native_run.py",
    "advanced/composable_strategies.py",
    "advanced/multiple_time_frames.py",
    "advanced/parameter_optimization.py",
)
ML = "advanced/machine_learning.py"


def read_index(root):
    """Parse only the selection table's three fixed columns; reject omissions, duplicates, and invalid categories."""
    text = (root / "README.md").read_text()
    rows = re.findall(
        r"^\| \[([^]]+\.py)\]\(([^)]+)\)\s*\|\s*([^|]+)\|\s*([^|]+)\|", text, re.MULTILINE
    )
    entries = {}
    for label, target, category, status in rows:
        assert label == target, f"Index label does not match path: {label}"
        assert target not in entries, f"Duplicate example: {target}"
        assert re.fullmatch(r"(?:strategies|advanced)/[a-z][a-z0-9_]*\.py", target), target
        assert category.strip() in ("Author script", "Imperative tutorial"), category
        assert status.strip() in ("Recommended", "Advanced", "Research only"), status
        entries[target] = (category.strip(), status.strip())
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*.py") if ".openbacktesting" not in p.relative_to(root).parts}
    assert entries and set(entries) == actual, f"Index does not match file set: {set(entries) ^ actual}"
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if not target.startswith(("https://", "http://", "#")):
            assert (root / unquote(target.split("#")[0])).exists(), f"Broken link: {target}"
    return entries


def test_index_and_execution_sets_match():
    entries = read_index(EXAMPLES)
    assert set(entries) == set(AUTHORS + TUTORIALS + (ML,))
    for path, (category, status) in entries.items():
        assert category == ("Author script" if path in AUTHORS else "Imperative tutorial")
        tree = ast.parse((EXAMPLES / path).read_text())
        assert ast.get_docstring(tree)
        # Only the custom-indicator topic may register original composed formulas; existing built-ins still use self.ta.
        custom_calls = {
            ast.unparse(node.args[0])
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
            and node.func.attr == "ind"
        }
        assert custom_calls == (
            {"mean_band"} if path == "strategies/custom_indicators.py" else set()
        )
        if path.startswith("strategies/"):
            assert category == "Author script" and status in ("Recommended", "Advanced")
            attributes = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute)]
            assert any(n.attr in ("close", "hlcc4") for n in attributes)
            assert any(n.attr == "ta" for n in attributes)
            # next extracts scalars before trade conditions; integer input validation in init is not an array comparison.
            next_nodes = (
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name == "next"
            )
            for compare in (
                n for method in next_nodes for n in ast.walk(method) if isinstance(n, ast.Compare)
            ):
                assert all(
                    not isinstance(n, ast.Attribute) for n in (compare.left, *compare.comparators)
                )
        else:
            assert status in ("Advanced", "Research only")
    assert entries[ML][1] == "Research only"


@pytest.mark.parametrize("defect", ["missing", "duplicate", "category", "status", "link", "name"])
def test_index_rejects_drift(tmp_path, defect):
    directory = tmp_path / "strategies"
    directory.mkdir()
    (directory / "sample.py").write_text('"""Example."""')
    row = "| [strategies/sample.py](strategies/sample.py) | Author script | Recommended |\n"
    text = row
    if defect == "missing":
        (directory / "extra.py").write_text("")
    elif defect == "duplicate":
        text += row
    elif defect == "category":
        text = text.replace("Author script", "unknown")
    elif defect == "status":
        text = text.replace("Recommended", "unknown")
    elif defect == "link":
        text += "[Broken](missing.md)\n"
    else:
        (directory / "sample.py").rename(directory / "Bad Name.py")
        text = text.replace("sample.py", "Bad Name.py")
    (tmp_path / "README.md").write_text(text)
    with pytest.raises(AssertionError):
        read_index(tmp_path)


def test_index_accepts_additional_examples(tmp_path):
    (tmp_path / "advanced").mkdir()
    rows = []
    for name in ("one", "two", "three"):
        relative = f"advanced/{name}.py"
        (tmp_path / relative).write_text('"""New feature example."""')
        rows.append(f"| [{relative}]({relative}) | Author script | Advanced |")
    (tmp_path / "README.md").write_text("\n".join(rows))
    assert len(read_index(tmp_path)) == len(rows)


@pytest.mark.parametrize("relative", AUTHORS + TUTORIALS + (ML,))
def test_loading_has_no_execution_or_optional_dependency(relative, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Loading examples must not compute, access the network, or write output")

    original_import = builtins.__import__
    original_open = builtins.open

    def guarded_import(name, *args, **kwargs):
        if name.split(".")[0] in ("sklearn", "sambo"):
            raise AssertionError("Loading definitions must not require optional dependencies")
        return original_import(name, *args, **kwargs)

    def readonly_open(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in "wax+"):
            forbidden()
        return original_open(file, mode, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Backtest, "__init__", forbidden)
        patch.setattr(Backtest, "run", forbidden)
        patch.setattr(Backtest, "optimize", forbidden)
        patch.setattr(Strategy, "__init__", forbidden)
        patch.setattr(socket.socket, "connect", forbidden)
        patch.setattr(subprocess, "Popen", forbidden)
        patch.setattr(webbrowser, "open", forbidden)
        patch.setattr(builtins, "__import__", guarded_import)
        patch.setattr(builtins, "open", readonly_open)
        patch.setattr(io, "open", readonly_open)
        namespace = runpy.run_path(str(EXAMPLES / relative))
        if relative in AUTHORS:
            runtime.describe(namespace)
            assert "bt" not in namespace
        else:
            assert callable(namespace["main"])


@pytest.mark.parametrize("relative", AUTHORS)
def test_author_execution(relative):
    namespace = runpy.run_path(str(EXAMPLES / relative))
    runtime.describe(namespace)
    stats = runtime.run(namespace, **example_chart(namespace))
    assert len(stats["_equity_curve"]) == len(example_chart(namespace)["data"])
    assert stats["_strategy"]._indicator_cursor.length == len(example_chart(namespace)["data"])


def test_custom_indicators_example_execution(monkeypatch):
    namespace = runpy.run_path(str(EXAMPLES / "strategies/custom_indicators.py"))
    cls = namespace["CustomIndicators"]
    original = cls.next
    seen = []

    def checked_next(self):
        seen.append(len(self.data))
        for line in (
            self.fast["middle"],
            self.slow["upper"],
            self.smoothed,
            *self.short_trend,
            *self.long_trend,
        ):
            assert len(line) == len(self.data)
        assert bool(
            self.short_trend.cross.valid[-1] and self.short_trend.cross[-1]
        ) == self.ta.is_crossover(self.short_trend.fast, self.short_trend.slow)
        original(self)

    monkeypatch.setattr(cls, "next", checked_next)
    stats = runtime.run(namespace, **example_chart(namespace))
    assert seen and seen[-1] == 120
    assert stats["# Trades"] == 0
    owner = stats["_strategy"]
    assert owner.fast is not owner.slow
    data = example_chart(namespace)["data"]
    for handle, length, width in ((owner.fast, 5, 0.02), (owner.slow, 20, 0.04)):
        middle = data.Close.rolling(length).mean()
        for channel, multiplier in (("middle", 1), ("upper", 1 + width), ("lower", 1 - width)):
            np.testing.assert_allclose(handle[channel], middle * multiplier, equal_nan=True)
    expected_ema = compute(
        "ta.ema",
        data.assign(Middle=data.Close.rolling(5).mean()),
        parameters={"length": 3},
        inputs={"close": "Middle"},
    )
    np.testing.assert_allclose(owner.smoothed, expected_ema, equal_nan=True)
    payload = export_result(stats)
    assert len(payload["plots"]) == 2
    for source, length in zip(payload["sources"], (5, 20)):
        expected = data.Close.rolling(length).mean()
        assert source["values"][: length - 1] == [None] * (length - 1)
        np.testing.assert_allclose(source["values"][length - 1 :], expected.iloc[length - 1 :])
    other = Backtest(data, namespace["AnotherStrategy"]).run()["_strategy"]
    typical = (data.High + data.Low + data.Close) / 3
    np.testing.assert_allclose(other.band["middle"], typical.rolling(10).mean(), equal_nan=True)
    assert other.band._cursor is not owner.fast._cursor


def test_cross_signals_example_execution(monkeypatch):
    namespace = runpy.run_path(str(EXAMPLES / "strategies/cross_signals.py"))
    cls = namespace["CrossSignals"]
    original = cls.next
    counts = {"cross": 0, "crossover": 0, "crossunder": 0}

    def checked_next(self):
        for name, signal in (
            ("cross", self.crosses),
            ("crossover", self.up),
            ("crossunder", self.down),
        ):
            value = getattr(self.ta, "is_" + name)(self.fast, self.slow)
            assert value is bool(signal.valid[-1] and signal[-1])
            counts[name] += value
        original(self)

    monkeypatch.setattr(cls, "next", checked_next)
    stats = runtime.run(namespace, **example_chart(namespace))
    assert all(count > 0 for count in counts.values())
    assert counts["cross"] == counts["crossover"] + counts["crossunder"]
    assert stats["# Trades"] > 0


@pytest.mark.parametrize("relative", TUTORIALS)
def test_tutorial_execution(relative, tmp_path):
    optimizer = relative == "advanced/optimizer_results.py"
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / relative)]
        + (["--output", str(tmp_path / "results.db")] if optimizer else []),
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stderr
    if optimizer:
        from openbacktesting.optimizer import open_result

        saved = open_result(tmp_path / "results.db")
        assert saved.info()["committed"] == 6
        assert len(saved.query(order_by=["summary.all.totalReturn.value"])["rows"]) == 6
        return
    assert "Return [%]" in result.stdout and "# Trades" in result.stdout
    assert not list(tmp_path.iterdir())


def test_chart_timezone_example_results(capsys):
    tutorial = runpy.run_path(str(EXAMPLES / "advanced/chart_context.py"))
    result = tutorial["timezone_examples"]()
    assert result["local"]["Asia/Shanghai"]["# Trades"] == 1
    assert result["local"]["UTC"]["# Trades"] == 0
    repeated = result["dst"]["_equity_curve"].index[1:3]
    assert [time.hour for time in repeated] == [1, 1]
    assert repeated[0].utcoffset() != repeated[1].utcoffset()
    assert repeated.tz_convert("UTC").hour.tolist() == [5, 6]
    for zone, ends in [
        ("UTC", [1000.0, 1005.0, 1015.0]),
        ("Asia/Shanghai", [1000.0, 1010.0, 1015.0]),
    ]:
        stats = result["statistics"][zone]
        assert stats["_equity_curve"].Equity.resample("D").last().tolist() == ends
        assert stats.attrs["backtest_snapshot"]["context"]["timezone"] == zone
    output = capsys.readouterr().out
    assert "Repeated New York hour" in output and "daily closing equity" in output


def test_readme_runtime_recipe(monkeypatch, tmp_path):
    text = (EXAMPLES / "README.md").read_text()
    recipe = re.search(r"```python\n(.*?)\n```", text, re.DOTALL).group(1)
    monkeypatch.chdir(ENGINE)
    script = tmp_path / "recipe.py"
    script.write_text(recipe)
    namespace = runpy.run_path(str(script))
    assert len(namespace["result"]["_equity_curve"]) == len(GOOG)
    assert namespace["result"].attrs["input_snapshot"]["values"]["Moving-average period"] == 20


def test_saved_sources_execution(monkeypatch):
    namespace = runpy.run_path(str(EXAMPLES / "strategies/data_sources.py"))
    original = namespace["DataSources"].next
    seen = []

    def checked(self):
        size = len(self.close)
        assert self.saved_close is self.close
        np.testing.assert_array_equal(np.asarray(self.saved_close), GOOG.Close.iloc[:size])
        assert len(self.smoothed) == size
        assert self.hlcc4[-1] == (self.high[-1] + self.low[-1] + 2 * self.close[-1]) / 4
        seen.append(size)
        original(self)

    monkeypatch.setattr(namespace["DataSources"], "next", checked)
    stats = runtime.run(namespace, **example_chart(namespace))
    assert len(seen) > 1000 and seen[-1] == len(GOOG)
    assert stats["# Trades"] > 0


@pytest.mark.parametrize(
    "filename,class_name,params",
    [
        ("native_run", "SmaCross", {}),
        ("native_run", "SmaCross", {"n1": 5, "n2": 30}),
        ("composable_strategies", "SmaCross", {}),
        ("composable_strategies", "SmaCross", {"n1": 7, "n2": 40}),
        ("multiple_time_frames", "System", {}),
        ("multiple_time_frames", "System", {"d_rsi": 10, "w_rsi": 15, "level": 50}),
        ("parameter_optimization", "Sma4Cross", {}),
        *[
            ("parameter_optimization", "Sma4Cross", {"n1": n1, "n2": n2})
            for n1 in (40, 50)
            for n2 in (80, 100)
        ],
    ],
)
def test_builtin_sma_preserves_example_behavior(filename, class_name, params, monkeypatch):
    namespace = runpy.run_path(str(EXAMPLES / f"advanced/{filename}.py"))
    strategy = namespace[class_name]
    actual = Backtest(GOOG, strategy, commission=0.002).run(**params)
    assert any(
        indicator.metadata["id"] == "ta.sma" for indicator in actual["_strategy"]._indicators
    )

    def legacy_sma(namespace, source, *, length):
        # Independently reproduce the pre-migration pandas rolling + self.ind path without calling the built-in backend.
        owner = namespace._register.__self__
        return owner.ind(
            lambda values: pd.Series(values).rolling(length).mean().to_numpy(),
            np.asarray(source),
        )

    monkeypatch.setattr(TechnicalAnalysis, "sma", legacy_sma)
    expected = Backtest(GOOG, strategy, commission=0.002).run(**params)
    actual_indicators = actual["_strategy"]._indicators
    expected_indicators = expected["_strategy"]._indicators
    assert len(actual_indicators) == len(expected_indicators)
    for builtin, legacy in zip(actual_indicators, expected_indicators):
        # Compare both values and the NaN warmup prefix; base-class signals and ATR must also remain consistent.
        np.testing.assert_array_equal(np.asarray(builtin), np.asarray(legacy))
    # Indicator columns vary with registration names; compare complete fill records column by column, having checked indicator values separately above.
    trade_columns = [
        "Size",
        "EntryBar",
        "ExitBar",
        "EntryPrice",
        "ExitPrice",
        "SL",
        "TP",
        "PnL",
        "Commission",
        "ReturnPct",
        "EntryTime",
        "ExitTime",
        "Duration",
        "Tag",
    ]
    pd.testing.assert_frame_equal(
        actual["_trades"][trade_columns], expected["_trades"][trade_columns]
    )
    pd.testing.assert_frame_equal(actual["_equity_curve"], expected["_equity_curve"])


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {
            "Show highlights": True,
            "Moving-average period": 5,
            "Highlight multiplier": 1.01,
            "Price source": "hl2",
            "Moving-average type": "SMA",
            "Reference price": 120.5,
            "Highlight start": 1096502400000,
            "Session description": "0930-1600:23456",
            "Moving-average color": "#abcdef",
        },
        {"Show highlights": False},
        {"Highlight start": 4102444800000},
        {"Highlight multiplier": 2.0},
    ],
)
def test_all_inputs_example_execution(overrides):
    namespace = runpy.run_path(str(EXAMPLES / "strategies/all_inputs.py"))
    schema = runtime.describe(namespace)
    assert {field["kind"] for field in schema["inputs"]} == {
        "bool",
        "int",
        "float",
        "string",
        "enum",
        "price",
        "time",
        "session",
        "color",
    }
    request = {key: schema[key] for key in ("schemaVersion", "schemaHash")}
    request["values"] = overrides
    chart = example_chart(namespace)
    stats = runtime.run(namespace, request, **chart)
    owner = stats["_strategy"]
    values = stats.attrs["input_snapshot"]["values"]
    expected_values = {field["title"]: field["default"] for field in schema["inputs"]} | overrides
    expected_values["Moving-average color"] = Color.from_hex(expected_values["Moving-average color"]).to_hex()
    assert values == expected_values
    assert owner.average_kind is namespace["AverageKind"][values["Moving-average type"]]
    assert isinstance(owner.line_color, Color)
    assert owner.session == values["Session description"]
    assert len(stats["_equity_curve"]) == 120  # session does not filter input market data.
    assert stats["# Trades"] == 0

    data = chart["data"]
    source = data.Close if values["Price source"] == "close" else (data.High + data.Low) / 2
    length = values["Moving-average period"]
    if values["Moving-average type"] == "SMA":
        expected = source.rolling(length).mean()
    else:
        seeded = source.copy()
        seeded.iloc[: length - 1] = np.nan
        seeded.iloc[length - 1] = source.iloc[:length].mean()
        expected = seeded.ewm(span=length, adjust=False).mean()
    np.testing.assert_allclose(owner.average, expected, equal_nan=True)
    payload = export_result(stats)
    assert payload["plots"][0]["color"] == values["Moving-average color"]
    assert payload["plots"][1]["value"] == values["Reference price"]
    mask = (
        (data.Close > expected * values["Highlight multiplier"])
        & (data.index >= pd.to_datetime(values["Highlight start"], unit="ms", utc=True))
        & values["Show highlights"]
    )
    events = payload["colorEvents"]
    assert [event["knownAtBar"] for event in events] == np.flatnonzero(mask).tolist()
    if not overrides or "Moving-average type" in overrides:
        assert events
    assert all(event["color"] == owner.background.to_hex() for event in events)


@pytest.mark.parametrize("fast,slow", [(12, 26), (5, 30)])
def test_builtin_ema_inputs(fast, slow):
    namespace = runpy.run_path(str(EXAMPLES / "strategies/ema_inputs.py"))
    schema = runtime.describe(namespace)
    request = {key: schema[key] for key in ("schemaVersion", "schemaHash")}
    request["values"] = {"Fast period": fast, "Slow period": slow}
    stats = runtime.run(namespace, request, **example_chart(namespace))
    strategy = stats["_strategy"]
    for handle, length in ((strategy.fast_line, fast), (strategy.slow_line, slow)):
        assert handle.metadata["id"] == "ta.ema"
        assert handle.metadata["parameters"]["length"] == length
        # Independently verify the default SMA seed, warmup, and subsequent recurrence; the old custom EMA baseline no longer applies.
        expected = GOOG.Close.copy()
        seed = expected.iloc[:length].mean()
        expected.iloc[: length - 1] = np.nan
        expected.iloc[length - 1] = seed
        expected = expected.ewm(span=length, adjust=False).mean()
        np.testing.assert_array_equal(np.asarray(handle), expected.to_numpy())
    assert stats["# Trades"] > 0


def test_builtin_rsi_resampling_has_no_future_values():
    namespace = runpy.run_path(str(EXAMPLES / "advanced/multiple_time_frames.py"))
    strategy = namespace["System"]
    full = Backtest(GOOG, strategy).run()["_strategy"]
    expected_daily = compute("ta.rsi", GOOG, parameters={"length": 30})
    assert full.daily_rsi.metadata["id"] == "ta.rsi"
    np.testing.assert_array_equal(np.asarray(full.daily_rsi), np.asarray(expected_daily))
    weekly = GOOG.Close.resample("W-FRI", label="right").last().dropna()
    expected_weekly = compute("ta.rsi", weekly.to_frame("Close"), parameters={"length": 30}).s
    aligned = expected_weekly.reindex(GOOG.index, method="ffill")
    np.testing.assert_array_equal(np.asarray(full.weekly_rsi), aligned.to_numpy())
    assert aligned.first_valid_index() == expected_weekly.first_valid_index()
    # Truncate data on different weekdays; an incomplete week must not leak full-week results.
    for stop in range(400, 407):
        partial = Backtest(GOOG.iloc[:stop], strategy).run()["_strategy"]
        np.testing.assert_array_equal(
            np.asarray(partial.weekly_rsi), np.asarray(full.weekly_rsi)[:stop]
        )


def test_optimizer_choices_and_budget(monkeypatch):
    namespace = runpy.run_path(str(EXAMPLES / "advanced/parameter_optimization.py"))
    calls = []

    def optimize(self, **kwargs):
        calls.append(kwargs)
        heatmap = pd.Series(
            [1.0, 2.0, 3.0, 4.0],
            index=pd.MultiIndex.from_product([[40, 50], [80, 100]], names=["n1", "n2"]),
        )
        result = (pd.Series({"# Trades": 1}), heatmap)
        return (*result, object()) if kwargs.get("return_optimization") else result

    monkeypatch.setattr(Backtest, "optimize", optimize)
    namespace["main"]()
    call = calls.pop()
    assert "method" not in call
    assert np.prod([len(call[name]) for name in ("n1", "n2", "n_enter", "n_exit")]) == 4
    pytest.importorskip("sambo")
    namespace["main"]("sambo")
    call = calls.pop()
    assert call["method"] == "sambo" and call["max_tries"] == 40 and call["random_state"] == 0
    with pytest.raises(ValueError, match="method"):
        namespace["main"]("invalid")


@pytest.mark.parametrize(
    "relative,dependency,extra",
    [
        (ML, "sklearn", "test"),
        ("advanced/parameter_optimization.py", "sambo", "optimize"),
    ],
)
def test_missing_optional_dependency(relative, dependency, extra, monkeypatch):
    namespace = runpy.run_path(str(EXAMPLES / relative))
    original = builtins.__import__

    def missing(name, *args, **kwargs):
        if name.split(".")[0] == dependency:
            raise ImportError("Test missing dependency")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    with pytest.raises(RuntimeError, match=re.escape(f"openbacktesting[{extra}]")):
        namespace["main"](*(["sambo"] if dependency == "sambo" else []))


def test_ml_builtin_features_preserve_definition():
    namespace = runpy.run_path(str(EXAMPLES / ML))
    data = namespace["EURUSD"]
    features = namespace["prepare_data"]()
    for length in (10, 20, 50, 100):
        expected = (data.Close - data.Close.rolling(length).mean()) / data.Close
        np.testing.assert_array_equal(features[f"X_SMA{length}"], expected.loc[features.index])
    hlc3 = (data.High + data.Low + data.Close) / 3
    middle = hlc3.rolling(20).mean()
    deviation = hlc3.rolling(20).std(ddof=1)
    upper, lower = middle + 2 * deviation, middle - 2 * deviation
    for name, expected in {
        "X_BB_upper": (upper - data.Close) / data.Close,
        "X_BB_lower": (lower - data.Close) / data.Close,
        "X_BB_width": (upper - lower) / data.Close,
    }.items():
        # Built-in variance and pandas rolling.std differ in floating-point rounding.
        np.testing.assert_allclose(features[name], expected.loc[features.index], rtol=0, atol=1e-10)


def test_ml_execution_light(monkeypatch):
    pytest.importorskip("sklearn")
    namespace = runpy.run_path(str(EXAMPLES / ML))
    globals_ = namespace["main"].__globals__
    monkeypatch.setitem(globals_, "EURUSD", globals_["EURUSD"].iloc[:650])
    once, rolling = namespace["main"]()
    for stats in (once, rolling):
        assert len(stats["_equity_curve"]) == 551
        assert np.isfinite(stats["_strategy"].forecasts).sum() > 100


@pytest.mark.skipif(
    os.environ.get("OPENBACKTESTING_RUN_SLOW_EXAMPLES") != "1", reason="Explicitly enable the full slow ML example"
)
def test_ml_execution_slow(tmp_path):
    pytest.importorskip("sklearn")
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / ML)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert "One-time training:" in result.stdout and "Rolling training:" in result.stdout
    assert result.stdout.count("# Trades") == 2
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("relative", ["trading_lifecycle", "fractional_sizing", "managed_orders"])
def test_trading_examples_reconcile(relative):
    namespace = runpy.run_path(str(EXAMPLES / "strategies" / (relative + ".py")))
    result = runtime.run(namespace, **example_chart(namespace))
    if relative == "trading_lifecycle":
        assert result["_final_account"]["balance"] == 9988
        assert result["Commissions [$]"] == 12
        assert "Rejected" in result["_orders"].status.tolist()
        assert result["_open_trades"].empty
    elif relative == "fractional_sizing":
        sizes = result._order_sizing
        assert sizes["mode"].tolist() == ["amount", "percent", "qty", "qty"]
        assert sizes.source.tolist() == ["explicit", "explicit", "default", "explicit"]
        assert sizes.qty.tolist() == [0.2, 0.2, 0.1, 10]
        assert result["_strategy"].invalid_noop_rejected
        assert result["_fills"].qty.tolist() == [0.1, 0.1, 0.2]
        assert result["_fills"].price.tolist() == [100, 100, 100]
        assert result["_orders"].iloc[-1].reason == "reduce_only_remainder"
    else:
        assert result["_orders"].iloc[0].status == "Expired"
        assert result["_fills"].price.tolist() == [105.5, 103]
        sizes = result._order_sizing.iloc[-2:]
        assert sizes["mode"].tolist() == ["percent", "amount"]
        assert sizes.qty.tolist() == [1, 1]
        assert sizes.reference_price.tolist() == [100, 100]
        ids = sizes.order_id.tolist()
        assert result._orders.set_index("order_id").loc[ids].status.tolist() == [
            "Filled",
            "Canceled",
        ]
        assert result.attrs["diagnostics"][0]["code"] == "ambiguous_oco_bar"


def test_plotting_example_color_events(capsys):
    from openbacktesting import Color
    from openbacktesting.plotting import export_result

    namespace = runpy.run_path(str(EXAMPLES / "strategies/plotting.py"))
    result = runtime.run(namespace, **example_chart(namespace))
    assert type(result["_strategy"].up_color) is Color
    assert result.attrs["input_snapshot"]["values"]["Rising color"] == "#22AA44FF"
    payload = export_result(result)
    assert payload["plots"][0]["color"] == "#22AA44FF"
    assert any(e["color"] == "#22AA4426" for e in payload["colorEvents"])
    schema = runtime.describe(namespace)
    alternate = runtime.run(
        namespace,
        {key: schema[key] for key in ("schemaVersion", "schemaHash")}
        | {"values": {"Rising color": "#ABCDEFFF"}},
        **example_chart(namespace),
    )
    assert export_result(alternate)["plots"][0]["color"] == "#ABCDEFFF"
    assert alternate.attrs["input_snapshot"]["values"]["Rising color"] == "#ABCDEFFF"
    events = payload["colorEvents"]
    assert {e["kind"] for e in events} == {"background", "bar"}
    assert any(e["pane"] != "main" and e["kind"] == "background" for e in events)
    assert any(e["color"] is None for e in events)
    assert any(e["color"] == "#22AA4400" for e in events)
    assert [e["color"] for e in events if e["knownAtBar"] == 60 and e["kind"] == "bar"][-1] is None
    tutorial = runpy.run_path(str(EXAMPLES / "advanced/plotting_export.py"))
    assert tutorial["main"]()["colorEvents"] == events
    assert "color events" in capsys.readouterr().out


def test_bar_states_example_execution():
    from openbacktesting import BarState

    namespace = runpy.run_path(str(EXAMPLES / "strategies/bar_states.py"))
    chart = example_chart(namespace)
    result = runtime.run(namespace, **chart)
    owner = result["_strategy"]
    rows = owner.observed
    assert [row[0] for row in rows] == list(range(len(chart["data"])))
    assert [row[1] for row in rows] == list(chart["data"].index)
    assert rows[0][2] == BarState(True, False)
    assert rows[-1][2] == BarState(False, True)
    assert len(owner.above_average) == len(rows) - 2
    payload = export_result(result)
    assert [event["anchorBar"] for event in payload["colorEvents"]] == [0, len(rows) - 1]
    assert all(payload["execution"]["strategyNext"])


def test_strategy_logs_example_execution():
    namespace = runpy.run_path(str(EXAMPLES / "advanced/strategy_logs.py"))
    records = namespace["main"]()
    assert set(records) == {"success", "failed", "hosted"}
    for rows in records.values():
        assert rows[0]["phase"] == "init" and rows[-1]["phase"] == "on_finish"
        assert rows[0]["bar_index"] is None
        for row in rows:
            assert Path(row["source_file"]).name == "strategy_logs.py"
            line = Path(row["source_file"]).read_text().splitlines()[row["source_line"] - 1]
            assert "self.log." in line
            assert row["recorded_at"].endswith("+00:00")
    assert len(records["failed"]) < len(records["success"])


def test_local_builtin_examples_values():
    helper = runpy.run_path(str(EXAMPLES / "strategies/local_value_helpers.py"))
    result = runtime.run(helper, **example_chart(helper))
    assert result._strategy.rounded == 100.05
    payload = export_result(result)
    assert len(payload["colorEvents"]) == 14
    assert {e["kind"] for e in payload["colorEvents"]} == {"bar", "background"}
    assert result._orders.iloc[0].status == "Canceled"
    assert result._orders.iloc[0].limit == 100.05

    indicator = runpy.run_path(str(EXAMPLES / "strategies/local_builtin_indicators.py"))
    chart = example_chart(indicator)
    result = runtime.run(indicator, **chart)
    owner = result._strategy
    assert len(owner.observed) == 8
    assert owner.observed[0][:5] == (2.0, 100.0, 100.0, 100.0, 100.0)
    assert owner.observed[0][-1] == 100.0
    np.testing.assert_array_equal(owner.weighted, owner.bands.vwap)
    assert owner.weighted[1] == pytest.approx(108.0)
    assert owner.bands.upper[1] == pytest.approx(108.0 + np.sqrt(32.0))
    assert owner.regime[-1] == 0
    # Average prices agree; only the range branch produces different bands on gap data.
    original = compute("ta.kc", chart["data"], parameters={"length": 3})
    assert not np.allclose(owner.channel.upper, original[2], equal_nan=True)

    closed = runpy.run_path(str(EXAMPLES / "strategies/closed_trade_statistics.py"))
    result = runtime.run(closed, **example_chart(closed))
    owner = result._strategy
    assert result._trades.PnL.tolist() == [10.0, -4.0, 0.0]
    assert owner.final.net_profit == result._trades.PnL.sum() == 6.0
    assert owner.final.closed_count == len(result._trades) == 3
    assert [s.closed_count for s in owner.snapshots] == [0, 0, 1, 2, 3]
    assert owner.initial.closed_count == 0


def test_portfolio_report_example():
    report = runpy.run_path(str(EXAMPLES / "advanced/portfolio_report.py"))["main"]()
    assert report["summary"]["all"]["totalPnl"]["value"] == 30
    assert report["summary"]["all"]["closedFragmentCount"]["value"] == 2
