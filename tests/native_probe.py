"""Native-semantics observer with fixed input; runnable against any compatible baseline package."""

import argparse
import importlib
import json
import math

import numpy as np
import pandas as pd


def observe(package="openbacktesting"):
    api = importlib.import_module(package)
    result = {}
    for case in ["warmup", "netting", "bracket", "close"]:
        frame = pd.DataFrame(
            {"Open": [100.0] * 7, "High": [102.0] * 7, "Low": [98.0] * 7, "Close": [100.0] * 7},
            index=pd.date_range("2024-01-01", periods=7),
        )
        if case == "bracket":
            frame.iloc[2] = [104.0, 106.0, 94.0, 100.0]
        seen = []

        class Probe(api.Strategy):
            scenario = case
            callbacks = seen

            def init(self):
                if self.scenario == "warmup":
                    self.signal = self.ind(lambda: np.array([np.nan, np.nan, 1, 1, 1, 1, 1]))

            def next(self):
                bar = len(self.data) - 1
                self.callbacks.append([bar, float(self.position.size), float(self.equity)])
                if self.scenario == "netting":
                    if bar == 1:
                        self.buy(qty=5)
                    elif bar == 2:
                        self.sell(qty=2)
                elif self.scenario == "bracket" and bar == 1:
                    self.buy(qty=1, sl=95, tp=105)
                elif self.scenario == "close":
                    if bar == 1:
                        self.buy(qty=1)
                    elif bar == 3:
                        self.position.close()

        stats = api.Backtest(
            frame, Probe, execution_timing=("same_close" if case == "close" else "next_open")
        ).run()
        trades = stats["_trades"][
            ["Size", "EntryBar", "ExitBar", "EntryPrice", "ExitPrice", "PnL", "Commission"]
        ]
        result[case] = {
            "callbacks": seen,
            "trades": trades.to_dict("records"),
            "equity": stats["_equity_curve"]["Equity"].tolist(),
            "statistics": {
                key: float(stats[key]) for key in ["Equity Final [$]", "Return [%]", "# Trades"]
            },
        }
    return result


def normalize(value):
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", default="openbacktesting")
    args = parser.parse_args()
    print(json.dumps(normalize(observe(args.package)), indent=2, allow_nan=False))
