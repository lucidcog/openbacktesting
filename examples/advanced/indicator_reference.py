"""Explore indicators individually: register one indicator against the same offline data and read its output channels.

Additional inputs demonstrate binding only, not real benchmarks or exchange periods. No trades or commission;
required_outputs=[] allows sparse outputs to be observed; check valid on each channel before reading.
"""

import argparse

import numpy as np

from openbacktesting import Backtest, Strategy
from openbacktesting.indicators import describe
from openbacktesting.test import GOOG


def make_data():
    data = GOOG.copy()
    data["source"] = data.Close
    data["benchmark"] = data.Close.shift(1)  # Example series; replace with a real benchmark on the same calendar
    data["periods"] = 10.0
    data["fast"] = data.Close.rolling(3).mean()
    data["slow"] = data.Close.rolling(10).mean()
    data["left"] = data["fast"]
    data["right"] = data["slow"]
    data["condition"] = (data.Close > data.Open).astype(float)
    data["trend"] = data["condition"]
    data["signal"] = data.Close.pct_change() * 100
    data["anchor"] = (np.arange(len(data)) % 20 == 0).astype(float)
    return data


def main(indicator="ta.ema"):
    spec = describe(indicator)
    if spec.status != "available":
        raise ValueError(f"{indicator}: {spec.reason}")

    class ObserveIndicator(Strategy):
        def init(self):
            self.value = getattr(self.ta, indicator.removeprefix("ta."))(required_outputs=[])
            self.latest = {}

        def next(self):
            for channel in spec.outputs:
                handle = self.value if len(spec.outputs) == 1 else self.value[channel]
                if handle.valid[-1]:
                    self.latest[channel] = float(handle[-1])

    result = Backtest(make_data(), ObserveIndicator).run()
    print(result[["Return [%]", "# Trades"]])
    print(indicator, result["_strategy"].latest)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--indicator", default="ta.ema")
    main(parser.parse_args().indicator)
