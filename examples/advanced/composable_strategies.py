"""Combine SignalStrategy and TrailingStrategy: vector entry signals with a trailing stop.

Bundled GOOG daily data, with no additional dependencies; n1/n2 are fast/slow SMA periods. Call super when overriding init/next.
Long only; each request uses 95% of equity, with a 2 ATR trailing stop and 0.2% commission.
No forced end-of-run liquidation. Explicitly run main to print statistics; a stop does not guarantee profit.
"""

import pandas as pd

from openbacktesting import Backtest
from openbacktesting.lib import SignalStrategy, TrailingStrategy
from openbacktesting.test import GOOG


class SmaCross(SignalStrategy, TrailingStrategy):
    n1 = 10
    n2 = 25

    def init(self):
        super().init()
        sma1 = self.ta.sma(self.close, length=self.n1)
        sma2 = self.ta.sma(self.close, length=self.n2)
        signal = (pd.Series(sma1) > sma2).astype(int).diff().fillna(0)
        signal = signal.replace(-1, 0)
        self.entry_signal = signal.to_numpy()
        self.set_trailing_sl(2)

    def next(self):
        super().next()
        if self.entry_signal[len(self.data) - 1] > 0:
            self.buy(percent=95)


def main():
    stats = Backtest(GOOG, SmaCross, commission=0.002).run()
    print(stats)
    return stats


if __name__ == "__main__":
    main()
