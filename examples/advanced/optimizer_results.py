"""Select some inputs, save each Portfolio, cancel and resume, and sort results afterward.

Run: uv run --locked python examples/advanced/optimizer_results.py --output /tmp/optimizer-demo.db
output must be a new local file; logs and plots are not saved. The host loads code and supplies the actual execution identity.
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
    quantity = inputs.int(1, title="Quantity", minval=1)
    exit_bar = inputs.int(2, title="Exit bar")
    enabled = inputs.bool(True, title="Trading enabled")

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
        # Exit bar is not searched: every combination retains its current value 3 rather than the declared default 2.
        "request": request_for(Example, {"exit_bar": 3}),
    }
    search = {"Quantity": Range(1, 3, 1), "Trading enabled": Values([True, False])}
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
    assert all(row["inputs"]["Exit bar"] == 3 for row in by_return["rows"])
    portfolio = saved.load_portfolio(by_return["rows"][0]["trial_id"])
    assert "plotting_result" not in portfolio and "strategy_logs" not in portfolio
    return {
        "committed": 6,
        "experiment_id": saved.experiment_id,
        "best_return": by_return["rows"][0],
        "lowest_drawdown": by_drawdown["rows"][0],
    }


def main(path=None):
    """Keep the result database when path is supplied; otherwise demonstrate in a temporary directory and clean up."""
    if path is not None:
        return _demo(path)
    with TemporaryDirectory(prefix="optimizer-example-") as directory:
        return _demo(Path(directory) / "results.db")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    print(main(parser.parse_args().output))
