"""Native parameter optimization and scores: four grid combinations by default; --method sambo explicitly selects the optional optimizer.

Bundled GOOG daily data; grid needs no extra dependency and SAMBO requires the optimize extra. Ordinary class parameters support native optimization;
They are not migrated to inputs, which currently does not support SAMBO. n1/n2 are trend periods and n_enter/n_exit are entry/exit periods.
0.2% commission, no forced end-of-run liquidation, and final-equity maximization; a fixed seed does not establish out-of-sample validity.
Print the best run, scores, and means grouped by trend period; SAMBO makes at most 40 attempts and costs more.
"""

import argparse

from openbacktesting import Backtest, Strategy
from openbacktesting.test import GOOG


class Sma4Cross(Strategy):
    n1 = 50
    n2 = 100
    n_enter = 20
    n_exit = 10

    def init(self):
        self.sma1 = self.ta.sma(self.close, length=self.n1)
        self.sma2 = self.ta.sma(self.close, length=self.n2)
        self.sma_enter = self.ta.sma(self.close, length=self.n_enter)
        self.sma_exit = self.ta.sma(self.close, length=self.n_exit)

    def next(self):
        if not self.position:
            if self.sma1[-1] > self.sma2[-1]:
                if self.ta.is_crossover(self.data.Close, self.sma_enter):
                    self.buy(percent=95)
            elif self.ta.is_crossover(self.sma_enter, self.data.Close):
                self.sell(percent=95)
        elif (
            self.position.is_long
            and self.ta.is_crossover(self.sma_exit, self.data.Close)
            or (self.position.is_short and self.ta.is_crossover(self.data.Close, self.sma_exit))
        ):
            self.position.close()


def ordered_periods(params):
    return params.n_exit < params.n_enter < params.n1 < params.n2


def main(method="grid"):
    if method not in ("grid", "sambo"):
        raise ValueError("method must be grid or sambo")
    if method == "sambo":
        try:
            import sambo  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "SAMBO requires an extra dependency: pip install 'openbacktesting[optimize]'"
            ) from exc
    bt = Backtest(GOOG, Sma4Cross, commission=0.002)
    common = {
        "constraint": ordered_periods,
        "maximize": "Equity Final [$]",
        "random_state": 0,
        "return_heatmap": True,
    }
    if method == "grid":
        # 2 × 2 × 1 × 1: all four combinations satisfy the period constraints; no random sampling.
        stats, heatmap = bt.optimize(
            n1=[40, 50],
            n2=[80, 100],
            n_enter=[20],
            n_exit=[10],
            **common,
        )
        optimization = None
    else:
        stats, heatmap, optimization = bt.optimize(
            n1=[10, 100],
            n2=[20, 200],
            n_enter=[10, 40],
            n_exit=[10, 30],
            method="sambo",
            max_tries=40,
            return_optimization=True,
            **common,
        )
    print(stats)
    print(heatmap.sort_values().tail(3))
    print(heatmap.groupby(["n1", "n2"]).mean().unstack())
    return stats, heatmap, optimization


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=("grid", "sambo"), default="grid")
    main(parser.parse_args().method)
