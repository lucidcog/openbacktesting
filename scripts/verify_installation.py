"""在干净的制品安装环境执行回测、资源、序列化和持久化验收。"""

import argparse
import json
import multiprocessing as mp
import pickle
import sys
from importlib.metadata import distribution, version
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

import openbacktesting as api
from openbacktesting import Backtest, DataContext, Strategy, Timeframe, backtest, inputs
from openbacktesting.broker import InstrumentSpec
from openbacktesting.optimizer import ExecutionIdentity, OptimizationError, Values, open_result
from openbacktesting.runtime import optimize, resume_optimization
from openbacktesting.test import GOOG
from openbacktesting.test._test import SmaCross


@backtest()
class Probe(Strategy):
    quantity = inputs.int(1, title="数量", minval=1)

    def init(self):
        pass

    def next(self):
        if self.bar_index == 0:
            self.buy(qty=self.quantity)
        if self.bar_index == 2:
            self.position.close()


def spawn_probe(value):
    assert value is Backtest
    result = Backtest(GOOG.iloc[:100], SmaCross, end_policy="close_at_last_close").run()
    return value.__module__, int(result["# Trades"])


def verify_optimizer():
    from openbacktesting.optimizer.validation import validate_report

    prices = [100.0, 110.0, 95.0, 108.0, 112.0]
    data = pd.DataFrame(
        {key: prices for key in ("Open", "High", "Low", "Close")},
        index=pd.date_range("2026-01-01", periods=5, tz="UTC"),
    )
    identity = ExecutionIdentity("a" * 64, "b" * 64)
    with TemporaryDirectory(prefix="installation-optimizer-") as directory:
        path = Path(directory) / "results.db"
        options = {
            "path": path,
            "identity": identity,
            "data": data,
            "context": DataContext(Timeframe.days(1), "UTC"),
            "instrument": InstrumentSpec(),
        }
        events = []
        partial = optimize(
            globals(),
            {"数量": Values([1, 2])},
            **options,
            on_progress=events.append,
            cancel=lambda: len(events) == 1,
        )
        assert partial.info()["committed"] == 1
        resume_optimization(globals(), experiment_id=partial.experiment_id, **options)
        result = open_result(path)
        assert result.info()["committed"] == 2
        rows = result.query(order_by=["summary.all.totalReturn.value"])["rows"]
        portfolio = result.load_portfolio(rows[0]["trial_id"])
        validate_report(portfolio)
        assert portfolio["semantics"]["metricsDefinitionVersion"] == "openbacktesting_portfolio_v1"
        assert json.loads(json.dumps(portfolio, allow_nan=False)) == portfolio
        before = path.read_bytes()
        incompatible = options | {"identity": ExecutionIdentity("c" * 64, "b" * 64)}
        try:
            resume_optimization(globals(), experiment_id=result.experiment_id, **incompatible)
        except OptimizationError as error:
            assert "身份" in str(error)
        else:
            raise AssertionError("不匹配身份未拒绝续跑")
        assert path.read_bytes() == before
    return {"committed": 2, "portfolio_roundtrip": True, "identity_rejection": True}


def verify_optional(mode):
    bt = Backtest(GOOG.iloc[:100], SmaCross, end_policy="close_at_last_close")
    if mode == "base":
        try:
            import sambo  # noqa: F401
        except ImportError:
            pass
        else:
            raise AssertionError("基础环境意外包含可选优化器")
        try:
            bt.optimize(fast=[5, 10], slow=[20, 30], method="sambo")
        except ImportError as error:
            assert "sambo" in str(error).lower()
        else:
            raise AssertionError("缺少优化器时未报告依赖错误")
        return "missing_dependency_error"
    result = bt.optimize(fast=[5, 10], slow=[20, 30], method="sambo", max_tries=10)
    assert isinstance(result, pd.Series)
    return "sambo_passed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("base", "optimize"), default="base")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package_path = Path(api.__file__).resolve()
    assert package_path.is_relative_to(Path(sys.prefix).resolve()), package_path
    assert "site-packages" in package_path.parts
    assert version("openbacktesting") == api.__version__ == "0.2.0"
    roots = {
        str(path).split("/", 1)[0]
        for path in distribution("openbacktesting").files
        if str(path).endswith("/__init__.py")
    }
    assert roots == {"openbacktesting"}, roots
    for name in (
        "py.typed",
        "indicators/catalog.json",
        "portfolio/catalog.json",
        "optimizer/portfolio-result.schema.json",
        "test/GOOG.csv",
        "test/BTCUSD.csv",
        "test/EURUSD.csv",
    ):
        assert files("openbacktesting").joinpath(name).is_file(), name
    for value in (Backtest, Strategy, Probe):
        assert pickle.loads(pickle.dumps(value)) is value
    assert Backtest.__module__.startswith("openbacktesting.")
    result = Backtest(GOOG.iloc[:100], SmaCross, end_policy="close_at_last_close").run()
    assert isinstance(result, pd.Series)
    with mp.get_context("spawn").Pool(1) as pool:
        module, trades = pool.apply(spawn_probe, (Backtest,))
    assert module.startswith("openbacktesting.") and trades == result["# Trades"]
    report = {
        "python": sys.version.split()[0],
        "package_version": api.__version__,
        "loaded_from_site_packages": True,
        "resources": True,
        "backtest": True,
        "pickle": True,
        "spawn": True,
        "optimizer": verify_optimizer(),
        "optional_optimizer": verify_optional(args.mode),
        "dependencies": {name: version(name) for name in ("numpy", "pandas", "pandas-ta-classic")},
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
