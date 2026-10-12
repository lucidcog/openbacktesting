"""Native backtest and result consumption: explicitly call main, unlike author templates that only export bt.

Bundled GOOG daily data, with no additional dependencies. Ordinary class parameters n1/n2 control built-in SMA periods;
This example retains the native API and bidirectional crossover strategy, with initial cash 10000, 0.2% commission, and no forced end-of-run liquidation.
Print statistics, the equity curve, and the trade table; see parameter_optimization.py in this directory for optimization.
"""

from openbacktesting import Backtest, Strategy
from openbacktesting.test import GOOG


class SmaCross(Strategy):
    n1 = 10
    n2 = 20

    def init(self):
        self.sma1 = self.ta.sma(self.close, length=self.n1)
        self.sma2 = self.ta.sma(self.close, length=self.n2)

    def next(self):
        if self.ta.is_crossover(self.sma1, self.sma2):
            self.position.close()
            self.buy(percent=95)
        elif self.ta.is_crossunder(self.sma1, self.sma2):
            self.position.close()
            self.sell(percent=95)


def main():
    bt = Backtest(GOOG, SmaCross, cash=10000, commission=0.002)
    stats = bt.run()
    print(stats)
    print(stats["_equity_curve"].tail())
    print(stats["_trades"].tail())
    return stats


if __name__ == "__main__":
    main()
