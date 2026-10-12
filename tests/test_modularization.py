"""Verify that module migration preserves legacy consumption, object paths, and optimization dispatch."""

import base64
import hashlib
import inspect
import io
import json
import pickle
import subprocess
import sys
from importlib import import_module
from pathlib import Path
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest
from openbacktesting._util import _Array, _Data, _Indicator

import openbacktesting as api
from openbacktesting import engine, lib
from openbacktesting.indicator_types import IndicatorHandle
from openbacktesting.test import GOOG
from openbacktesting.test._test import SmaCross

BASELINE = Path(__file__).with_name("modularization-baseline.json")


def inventory():
    classes = [engine.Strategy, engine.Position, engine.Order, engine.Trade, engine.Backtest]
    return {
        "engine_all": engine.__all__,
        "lib_all": lib.__all__,
        "classes": {cls.__name__: [cls.__module__, cls.__qualname__] for cls in classes},
        "signatures": {
            f"{cls.__name__}.{name}": str(inspect.signature(member))
            for cls in classes
            for name, member in vars(cls).items()
            if callable(member) and (not name.startswith("_") or name == "__init__")
        },
        "arrays": [[cls.__module__, cls.__qualname__] for cls in [_Array, _Indicator, _Data]],
    }


def baseline_objects():
    # Load only trusted SHA-256-backed samples generated in this repository before refactoring; never replace them with external input.
    baseline = json.loads(BASELINE.read_text())
    payload = base64.b64decode(baseline["pickle_base64"])
    assert hashlib.sha256(payload).hexdigest() == baseline["pickle_sha256"]

    # Fixture package roots are normalized; test-only mapping of the removed statistics class keeps historical objects and values verifiable.
    class HistoricalUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if module == "openbacktesting._stats":
                module = "openbacktesting.portfolio.stats"
            return super().find_class(module, name)

    return HistoricalUnpickler(io.BytesIO(payload)).load()


def assert_result(actual, expected):
    pd.testing.assert_series_equal(
        actual.filter(regex="^[^_]"), expected.filter(regex="^[^_]"), check_exact=True
    )
    for key in (
        "_orders",
        "_order_events",
        "_fills",
        "_trade_allocations",
        "_positions",
        "_account_curve",
        "_open_trades",
    ):
        pd.testing.assert_frame_equal(actual[key], expected[key], check_exact=True)
    assert actual["_final_account"] == expected["_final_account"]
    for name in ["_equity_curve", "_trades"]:
        pd.testing.assert_frame_equal(actual[name], expected[name], check_exact=True)
    assert str(actual["_strategy"]) == str(expected["_strategy"])


def test_original_exports_signatures_and_class_identity():
    expected = json.loads(BASELINE.read_text())["inventory"]
    # Keep historical baselines; this change explicitly removes the plotting API and makes warmup a calculation parameter.
    expected["lib_all"].remove("plot_heatmaps")
    expected["lib_all"].remove("cross")
    expected["lib_all"].remove("crossover")
    del expected["signatures"]["Backtest.plot"]
    expected["signatures"]["Strategy.I"] = (
        "(self, func: 'Callable', *args, name=None, **kwargs) -> 'IndicatorHandle'"
    )
    expected["signatures"]["Strategy.indicator"] = (
        "(self, indicator, *, inputs=None, backend=None, required_outputs=None, **parameters)"
    )
    expected["signatures"]["Backtest.__init__"] = expected["signatures"][
        "Backtest.__init__"
    ].replace("finalize_trades=False)", "finalize_trades=False, indicator_cache_bytes=67108864)")
    expected["signatures"]["Backtest.run_inputs"] = "(self, request) -> 'pd.Series'"
    expected["signatures"].update(
        json.loads(BASELINE.with_name("trading-v2-signatures.json").read_text())["methods"]
    )
    # Extend only data-only collection configuration; preserve historical baseline files.
    expected["signatures"]["Backtest.__init__"] = (
        expected["signatures"]["Backtest.__init__"][:-1]
        + ", context: 'DataContext | None' = None, plotting: 'bool' = True, plotting_limits: 'PlottingLimits | None' = None)"
    )
    # Retain both historical signature snapshots; the current public contract only renames and removes old entry points.
    expected["signatures"]["Strategy.ind"] = expected["signatures"].pop("Strategy.I")
    # The dynamic strategy-indicator entry point is removed; retain historical signature snapshots.
    del expected["signatures"]["Strategy.indicator"]
    # Strategy settings change only these three public method signatures; compare all others exactly.
    expected["signatures"]["Backtest.__init__"] = expected["signatures"][
        "Backtest.__init__"
    ].replace(
        "commission: 'float | tuple[float, float]' = 0.0,",
        "commission: 'float | tuple[float, float] | Commission | Callable[[float, float], float]' = 0.0, "
        "risk_free_rate: 'float' = 0.0, default_order_size: 'DefaultOrderSize | None' = None,",
    )
    for name in ("Strategy.buy", "Strategy.sell"):
        expected["signatures"][name] = expected["signatures"][name].replace(
            "qty: 'float',", "qty: 'float' = Ellipsis,"
        )
    expected["signatures"]["Strategy.ind"] = expected["signatures"]["Strategy.ind"].replace(
        ", warmup=True", ""
    )
    # Log queries add public signatures; the old baseline still checks the remaining entry points.
    expected["signatures"]["Backtest.get_logs"] = "(self) -> 'list[dict[str, str | int | None]]'"
    # Order entry points use explicit named fields; check new signatures exactly and retain historical snapshots.
    conditions = (
        "limit: 'float | None' = None, stop: 'float | None' = None, "
        "sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, "
        "reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, "
        "valid_bars: 'int | None' = None"
    )
    # Three sizing modes are mutually exclusive; the private omission sentinel differs from explicit None. Preserve historical snapshots.
    for name in ("Strategy.buy", "Strategy.sell"):
        expected["signatures"][name] = (
            "(self, *, qty: 'float' = <_Unset.VALUE: 'omitted'>, "
            "amount: 'float' = <_Unset.VALUE: 'omitted'>, "
            f"percent: 'float' = <_Unset.VALUE: 'omitted'>, {conditions}) -> 'Order'"
        )
    for unit in ("quantity", "value", "percent"):
        expected["signatures"][f"Strategy.order_target_{unit}"] = (
            f"(self, *, target: 'float', {conditions}) -> 'Order | None'"
        )
    expected["signatures"]["Strategy.submit_oco"] = (
        "(self, *, first: 'OrderRequest', second: 'OrderRequest') -> 'OrderGroup'"
    )
    expected["signatures"]["Order.__init__"] = expected["signatures"]["Order.__init__"].replace(
        "eligible=None)", "eligible=None, sizing=None)"
    )
    # The optimizer's private typed collection parameter enables all three collection categories by default; compare remaining signatures exactly.
    expected["signatures"]["Backtest.__init__"] = (
        expected["signatures"]["Backtest.__init__"][:-1]
        + ", _collection: 'CollectionPolicy' = CollectionPolicy(portfolio=True, logs=True, plotting=True))"
    )
    assert inventory() == expected
    assert api.Backtest is engine.Backtest
    assert api.Strategy is engine.Strategy
    assert lib.Backtest is engine.Backtest
    assert lib.Strategy is engine.Strategy


def test_pre_migration_objects_and_results():
    old = baseline_objects()
    assert old["classes"] == [engine.Backtest, engine.Strategy, engine.Order, engine.Trade]
    np.testing.assert_array_equal(old["indicator"], [1.0, 2.0])
    assert old["indicator"].name == "旧指标"
    pd.testing.assert_frame_equal(old["data"].df, GOOG.iloc[:4])
    bt = old["backtest"]
    assert type(bt) is engine.Backtest
    with pytest.raises(TypeError, match=r"Backtest state from 0\.1 cannot resume execution"):
        bt.run(fast=5, slow=10)
    current = api.Backtest(GOOG.iloc[:80], SmaCross, end_policy="close_at_last_close")
    result = current.run(fast=5, slow=10)
    restored = pickle.loads(pickle.dumps(current))
    assert type(restored) is engine.Backtest
    assert_result(restored.run(fast=5, slow=10), result)


def test_fixed_seed_optimization_matches_independent_runs():
    bt = api.Backtest(GOOG.iloc[:80], SmaCross, end_policy="close_at_last_close")
    expected = {(fast, slow): bt.run(fast=fast, slow=slow) for fast in (3, 5) for slow in (10, 15)}
    stats, heatmap = bt.optimize(fast=[3, 5], slow=[10, 15], random_state=42, return_heatmap=True)
    for pair, result in expected.items():
        assert heatmap.loc[pair] == pytest.approx(result["SQN"])
    assert_result(stats, expected[heatmap.idxmax()])


class InstrumentedBacktest(api.Backtest):
    calls: ClassVar[list] = []

    def run(self, **params):
        self.calls.append(params)
        return super().run(**params)

    @staticmethod
    def _mp_task(_):
        raise AssertionError("The original optimization entry point must not virtually dispatch to the subclass task method")


class InlinePool:
    def __init__(self, calls):
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def imap(self, task, args):
        self.calls.append(task)
        return map(task, args)


def test_pool_override_is_dynamic_and_run_remains_virtual(monkeypatch):
    bt = InstrumentedBacktest(GOOG.iloc[:80], SmaCross, end_policy="close_at_last_close")
    InstrumentedBacktest.calls = []
    first, second = [], []
    for calls in [first, second]:
        monkeypatch.setattr(api, "Pool", lambda calls=calls: InlinePool(calls))
        bt.optimize(fast=[3, 5], slow=[10], random_state=42)
        assert calls == [api.Backtest._mp_task]
    assert len(InstrumentedBacktest.calls) == 6
    assert all(set(params) == {"fast", "slow"} for params in InstrumentedBacktest.calls)


def test_lib_resampling_registers_indicator_without_new_wrapper():
    class Resampled(api.Strategy):
        def init(self):
            self.resampled = lib.resample_apply("2D", None, self.data.Close)

        def next(self):
            pass

    result = api.Backtest(GOOG.iloc[:40], Resampled).run()
    strategy = result["_strategy"]
    assert isinstance(strategy.resampled, IndicatorHandle)
    assert len(strategy._indicators) == 1
    assert strategy._indicators[0].name == strategy.resampled.name


def test_documentation_and_nested_type_keep_legacy_metadata():
    assert engine.Order.parent_trade.__doc__
    assert not hasattr(engine.Strategy, "_Strategy__FULL_EQUITY")
    assert engine.Backtest.run.__module__ == "openbacktesting.engine"


def test_shared_aggregation_objects_remain_mutable(monkeypatch):
    from openbacktesting import _aggregation

    for name in ["OHLCV_AGG", "TRADES_AGG"]:
        assert getattr(lib, name) is getattr(_aggregation, name)
    monkeypatch.setitem(lib.OHLCV_AGG, "Close", "first")
    values = pd.Series(
        [1.0, 2.0, 3.0, 4.0], index=pd.date_range("2024-01-01", periods=4), name="Close"
    )
    expected = values.resample("2D", label="right").first().reindex(values.index).ffill()
    actual = lib.resample_apply("2D", None, values)
    pd.testing.assert_series_equal(actual, expected, check_names=False)


@pytest.mark.parametrize("mode", ["default", "spawn"])
def test_real_subprocess_optimization_and_cleanup(mode):
    probe = Path(__file__).with_name("spawn_probe.py")
    result = subprocess.run(
        [sys.executable, str(probe), "--mode", mode],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    outcome = json.loads(result.stdout.splitlines()[-1])
    assert outcome["mode"] == mode
    assert outcome["status"] == "passed"
    assert outcome["exception_segments_released"] > 0


def test_renamed_modules_preserve_legacy_imports_and_pickle_paths():
    for name in (
        "aggregation",
        "broker",
        "data",
        "helpers",
        "optimization",
        "parallel",
        "strategy",
        "util",
    ):
        current = import_module(f"openbacktesting.{name}")
        legacy = import_module(f"openbacktesting._{name}")
        assert legacy is current
        assert getattr(api, f"_{name}") is current
    for module_name, names in {
        "portfolio.stats": ("_Stats", "compute_stats", "dummy_stats"),
    }.items():
        module = import_module(f"openbacktesting.{module_name}")
        for name in names:
            obj = getattr(module, name)
            assert obj.__module__ == f"openbacktesting.{module_name}"
            assert pickle.loads(pickle.dumps(obj)) is obj
