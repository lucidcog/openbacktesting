"""领域迁移前固定的定义、签名及受信任 pickle 契约。"""

import base64
import hashlib
import inspect
import io
import json
import pickle
import re
import runpy
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import numpy as np
import pytest
from openbacktesting import inputs, lib
from openbacktesting.strategy_data import StrategyData
from openbacktesting.test import GOOG

BASELINE = json.loads(Path(__file__).with_name("subpackages-baseline.json").read_text())


def test_old_definitions_keep_signatures_metadata_and_pickle():
    # 仅恢复本仓库在迁移前生成并校验摘要的样本。
    payload = base64.b64decode(BASELINE["pickle_base64"])
    assert hashlib.sha256(payload).hexdigest() == BASELINE["pickle_sha256"]

    # 样本仅规范化包根并重新固定摘要；测试内映射已迁移统计对象，删除的函数引用映射为 None。
    # 普通 pickle 不提供迁移支持，其失败由独立测试验证。
    class HistoricalUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if module == "openbacktesting.lib" and name in {"cross", "crossover"}:
                return None
            if module == "openbacktesting._stats":
                module = "openbacktesting.portfolio.stats"
            return super().find_class(module, name)

    restored = HistoricalUnpickler(io.BytesIO(payload)).load()
    expected_exports = [name for name in BASELINE["lib_all"] if name not in {"cross", "crossover"}]
    assert lib.__all__ == expected_exports
    for row in BASELINE["objects"]:
        if row["name"] in {"cross", "crossover"}:
            assert restored["references"][row["old"] + "." + row["name"]] is None
            continue
        obj = getattr(
            import_module(
                "openbacktesting."
                + ({"backtest": "engine", "stats": "portfolio.stats"}.get(row["old"], row["old"]))
            ),
            row["name"],
        )
        expected_module = row["module"]
        if row["old"] == "stats":
            expected_module = "openbacktesting.portfolio.stats"
        elif row["old"] == "lib" and row["name"] == "compute_stats":
            expected_module = "openbacktesting.portfolio.helpers"
        assert obj.__module__ == expected_module
        assert obj.__qualname__ == row["qualname"]
        if row["signature"] is not None:
            signature = re.sub(r"0x[0-9a-f]+", "<address>", str(inspect.signature(obj)))
            changes = json.loads(
                Path(__file__).with_name("trading-v2-signatures.json").read_text()
            )["objects"]
            expected = changes.get(row["old"] + "." + row["name"], row["signature"])
            if row["name"] == "Backtest":
                expected = (
                    expected[:-1]
                    + ", context: 'DataContext | None' = None, plotting: 'bool' = True, plotting_limits: 'PlottingLimits | None' = None)"
                )
                # 策略设置的显式签名增量；固定历史样本不重写。
                expected = expected.replace(
                    "commission: 'float | tuple[float, float]' = 0.0,",
                    "commission: 'float | tuple[float, float] | Commission | Callable[[float, float], float]' = 0.0, "
                    "risk_free_rate: 'float' = 0.0, default_order_size: 'DefaultOrderSize | None' = None,",
                )
                # 新增私有采集参数，默认值保持普通回测的原采集行为。
                expected = (
                    expected[:-1]
                    + ", _collection: 'CollectionPolicy' = CollectionPolicy(portfolio=True, logs=True, plotting=True))"
                )
            elif row["name"] == "Order":
                expected = expected.replace("eligible=None)", "eligible=None, sizing=None)")
            elif row["name"] == "compute_stats":
                expected = expected.replace(
                    "risk_free_rate: 'float' = 0.0", "risk_free_rate: 'float' = Ellipsis"
                )
            expected = expected.replace(
                "exposure: 'np.ndarray | None' = None)",
                "exposure: 'np.ndarray | None' = None, initial_equity: 'float' = Ellipsis)",
            )
            assert signature == expected
        assert restored["references"][row["old"] + "." + row["name"]] is obj
        assert pickle.loads(pickle.dumps(obj)) is obj
    assert type(restored["input"]) is inputs.InputSpec
    assert restored["input"].normalize(4) == 4
    assert restored["input"].title == "周期"
    assert restored["resolved"].snapshot() == {
        "schemaVersion": "1.0.0",
        "schemaHash": "baseline",
        "values": {"周期": 3},
        "overriddenTitles": ["周期"],
    }
    assert restored["resolved"].overrides() == {"length": 3}
    data = restored["data"]
    assert type(data) is StrategyData
    np.testing.assert_array_equal(data.get("close"), GOOG.Close.iloc[:4])
    np.testing.assert_array_equal(data.get("hl2"), (GOOG.High.iloc[:4] + GOOG.Low.iloc[:4]) / 2)
    data._cursor.length = 2
    assert len(data.get("close")) == 2
    assert not data._values["close"].flags.writeable


def test_new_paths_export_the_same_definitions_and_constants():
    for row in BASELINE["objects"]:
        if row["name"] in {"cross", "crossover"}:
            continue
        old = import_module(
            "openbacktesting."
            + ({"backtest": "engine", "stats": "portfolio.stats"}.get(row["old"], row["old"]))
        )
        new = import_module(
            "openbacktesting."
            + row["new"].replace("backtest.", "simulation.").replace("results.", "portfolio.")
        )
        assert getattr(old, row["name"]) is getattr(new, row["name"])
    for old, new, names in [
        ("aggregation", "data.aggregation", ["OHLCV_AGG", "TRADES_AGG"]),
        ("strategy_data", "data.strategy_data", ["PRICE_COLUMNS", "DATA_NAMES", "DERIVED"]),
        (
            "inputs",
            "strategy.inputs",
            ["bool", "color", "enum", "float", "int", "price", "session", "string", "time"],
        ),
    ]:
        for name in names:
            assert getattr(import_module("openbacktesting." + old), name) is getattr(
                import_module("openbacktesting." + new), name
            )
    assert lib.__pdoc__ == {
        "Strategy.__init__": False,
        "SignalStrategy.__init__": False,
        "TrailingStrategy.__init__": False,
    }


@pytest.mark.parametrize(
    "package, symbol, implementation",
    [
        ("strategy", "Strategy", "strategy.base"),
        ("simulation", "Backtest", "simulation.core"),
    ],
)
def test_parent_package_initialization_does_not_load_its_core(
    monkeypatch, package, symbol, implementation
):
    import builtins

    module = import_module("openbacktesting." + package)
    original = builtins.__import__
    calls = []

    def observed(name, *args, **kwargs):
        calls.append(name)
        return original(name, *args, **kwargs)

    # 独立执行父包入口，区分父包自身行为和既有包根急切导入。
    with monkeypatch.context() as patch:
        patch.setattr(builtins, "__import__", observed)
        namespace = runpy.run_path(module.__file__)
    assert "openbacktesting." + implementation not in calls
    assert symbol not in namespace
    assert namespace["__all__"] == (["BarState", symbol] if package == "strategy" else [symbol])
    expected = getattr(import_module("openbacktesting." + implementation), symbol)
    assert namespace["__getattr__"](symbol) is expected
    assert namespace["__getattr__"].__globals__[symbol] is expected
    with pytest.raises(AttributeError, match="missing"):
        namespace["__getattr__"]("missing")
    assert getattr(module, symbol) is expected


@pytest.mark.parametrize(
    "first",
    [
        "inputs",
        "strategy.inputs",
        "parallel",
        "simulation.parallel",
        "strategy.base",
        "simulation.core",
        "data.core",
        "broker.core",
        "portfolio.stats",
        "lib",
        "simulation",
        "_data",
    ],
)
def test_cold_cross_imports(first):
    code = """
import importlib, sys
importlib.import_module("openbacktesting." + sys.argv[1])
import openbacktesting as api
from openbacktesting.strategy.base import Strategy
from openbacktesting.simulation.core import Backtest
assert api.Strategy is Strategy and api.Backtest is Backtest
for name in ("data", "broker", "strategy", "parallel", "optimization"):
    current = importlib.import_module("openbacktesting." + name)
    assert importlib.import_module("openbacktesting._" + name) is current
"""
    result = subprocess.run(
        [sys.executable, "-c", code, first], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "name, names",
    [
        ("strategy", ["Strategy"]),
        ("simulation", ["Backtest"]),
        ("portfolio.stats", ["Strategy", "Trade"]),
    ],
)
def test_type_only_exports_resolve_to_existing_classes(monkeypatch, name, names):
    import typing

    from openbacktesting import engine

    module = import_module("openbacktesting." + name)
    with monkeypatch.context() as patch:
        patch.setattr(typing, "TYPE_CHECKING", True)
        namespace = runpy.run_path(module.__file__)
    for symbol in names:
        assert namespace[symbol] is getattr(engine, symbol)


@pytest.mark.parametrize("invalid", [False, True])
def test_legacy_numeric_index_conversion_keeps_success_and_value_error(monkeypatch, invalid):
    import pandas as pd
    from openbacktesting import Backtest
    from openbacktesting.test._test import SmaCross

    data = GOOG.iloc[:4].copy()
    data.index = pd.Index([1_700_000_000 + i * 86400 for i in range(4)])
    expected = pd.date_range("2023-11-14", periods=4)
    calls = []

    # 保留旧 pandas 接口分支；替身不代表当前 pandas 支持已删除的参数。
    monkeypatch.setattr(pd.Index, "is_numeric", lambda self: True, raising=False)

    def convert(index, *, infer_datetime_format):
        assert index.equals(data.index)
        assert infer_datetime_format is True
        calls.append(1)
        if invalid:
            raise ValueError("legacy conversion failed")
        return expected

    monkeypatch.setattr(pd, "to_datetime", convert)
    if invalid:
        with pytest.warns(UserWarning, match="datetime"):
            result = Backtest(data, SmaCross)
        assert result._data.index.equals(data.index)
    else:
        result = Backtest(data, SmaCross)
        assert result._data.index.equals(expected)
    assert calls == [1]


def test_resample_scalar_output_keeps_existing_rejection():
    with pytest.raises(AttributeError, match="index"):
        lib.resample_apply("2D", lambda values: np.array(1.0), GOOG.Close.iloc[:4])


@pytest.mark.parametrize("path", ["backtest", "backtest.core", "_backtest"])
def test_removed_module_paths_do_not_shadow_decorator(path):
    import openbacktesting as api

    with pytest.raises(ModuleNotFoundError):
        import_module("openbacktesting." + path)
    from openbacktesting import runtime, simulation

    assert callable(api.backtest)
    assert simulation.Backtest is api.Backtest and callable(runtime.discover)


@pytest.mark.parametrize(
    "path",
    [
        "results",
        "results.stats",
        "results.rates",
        "results.helpers",
        "results.trading",
        "stats",
        "_stats",
    ],
)
def test_removed_statistics_paths_and_current_pickle(path):
    import openbacktesting as api
    from openbacktesting.portfolio import helpers, stats

    assert not hasattr(api, path.split(".")[0])
    with pytest.raises(ModuleNotFoundError):
        import_module("openbacktesting." + path)
    for module, names in (
        (
            stats,
            (
                "_Stats",
                "compute_stats",
                "dummy_stats",
                "geometric_mean",
                "compute_drawdown_duration_peaks",
            ),
        ),
        (helpers, ("compute_stats",)),
    ):
        for name in names:
            obj = getattr(module, name)
            assert obj.__module__ == module.__name__
            assert pickle.loads(pickle.dumps(obj)) is obj
    value = stats._Stats({"Return [%]": 12.5})
    restored = pickle.loads(pickle.dumps(value))
    assert type(restored) is stats._Stats
    assert restored.equals(value)
    with pytest.raises(ModuleNotFoundError, match="openbacktesting._stats"):
        pickle.loads(b"copenbacktesting._stats\n_Stats\n.")
