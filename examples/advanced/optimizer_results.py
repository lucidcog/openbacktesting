"""选部分 inputs、逐份保存 Portfolio、取消恢复及事后排序。

运行：uv run --locked python examples/advanced/optimizer_results.py --output /tmp/optimizer-demo.db
output 必须是新本地文件；不保存日志或绘图。宿主负责加载代码并提供真实执行身份。
"""

import argparse
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from openbacktesting import DataContext, Strategy, Timeframe, backtest, inputs
from openbacktesting.broker import InstrumentSpec
from openbacktesting.data.timeframe import TimeframeUnit
from openbacktesting.optimizer import ExecutionIdentity, Range, Values, open_result
from openbacktesting.runtime import optimize, resume_optimization
from openbacktesting.strategy.inputs import request_for


@backtest()
class Example(Strategy):
    quantity = inputs.int(1, title="数量", minval=1)
    exit_bar = inputs.int(2, title="退出根")
    enabled = inputs.bool(True, title="交易开关")

    def init(self):
        pass

    def next(self):
        if self.enabled and self.bar_index == 0:
            self.buy(qty=self.quantity)
        if self.enabled and self.bar_index == self.exit_bar:
            self.position.close()


def _demo(path):
    prices = [100.0, 110.0, 95.0, 108.0, 112.0]
    data = pd.DataFrame(
        {k: prices for k in ("Open", "High", "Low", "Close")},
        index=pd.date_range("2026-01-01", periods=5, tz="UTC"),
    )
    options = {
        "path": path,
        "identity": ExecutionIdentity(
            hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            hashlib.sha256(b"no-local-dependencies").hexdigest(),
        ),
        "data": data,
        "context": DataContext(Timeframe(TimeframeUnit.DAY, 1), "UTC"),
        "instrument": InstrumentSpec(),
        # 退出根不参与搜索，所有组合保持当前值 3，而非声明默认 2。
        "request": request_for(Example, {"exit_bar": 3}),
    }
    search = {"数量": Range(1, 3, 1), "交易开关": Values([True, False])}
    saved_events = []

    def committed(event):
        saved_events.append(event)
        assert open_result(path).load_portfolio(event["trial_id"])

    partial = optimize(
        globals(), search, **options, on_progress=committed, cancel=lambda: len(saved_events) == 1
    )
    assert partial.info()["committed"] == 1
    resume_optimization(globals(), experiment_id=partial.experiment_id, **options)
    saved = open_result(path)
    by_return = saved.query(order_by=["summary.all.totalReturn.value"])
    by_drawdown = saved.query(order_by=["summary.all.maxDrawdownFraction.value"])
    assert saved.info()["committed"] == 6
    assert all(row["inputs"]["退出根"] == 3 for row in by_return["rows"])
    portfolio = saved.load_portfolio(by_return["rows"][0]["trial_id"])
    assert "plotting_result" not in portfolio and "strategy_logs" not in portfolio
    return {
        "committed": 6,
        "experiment_id": saved.experiment_id,
        "best_return": by_return["rows"][0],
        "lowest_drawdown": by_drawdown["rows"][0],
    }


def main(path=None):
    """指定 path 时保留结果库；省略时在临时目录演示并清理。"""
    if path is not None:
        return _demo(path)
    with TemporaryDirectory(prefix="optimizer-example-") as directory:
        return _demo(Path(directory) / "results.db")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    print(main(parser.parse_args().output))
