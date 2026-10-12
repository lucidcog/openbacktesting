"""Confirmed events and monthly anchors: an advanced author script combining indicators, patterns, and period levels through self.ta.

Bundled GOOG daily data, with no extra dependencies. A Pivot with three bars on each side appears only after right-side confirmation and cannot backdate trades.
PeriodStart marks each month's first input bar; the first month may be incomplete, so production data must ensure complete periods.
Exclusive orders and end-of-run liquidation, with default zero commission; this demonstrates mechanics rather than validating returns.
"""

from openbacktesting import EndPolicy, Strategy, backtest


@backtest(exclusive_orders=True, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class ExpandedSignals(Strategy):
    def init(self):
        self.fast = self.ta.ema(self.close, length=10)
        self.slow = self.ta.ema(self.close, length=30)
        self.cross = self.ta.crossover(self.fast, self.slow)
        self.smi = self.ta.smi_stochastic()
        self.pivot = self.ta.pivothigh(left=3, right=3)
        self.pattern = self.ta.cdl_engulfing()
        self.levels = self.ta.pivot_points(inputs={"anchor": "PeriodStart"}, method="traditional")

    def next(self):
        bullish = self.pattern.valid[-1] and self.pattern[-1] > 0
        if (
            self.cross.valid[-1]
            and self.cross[-1]
            and bullish
            and self.smi.smi.valid[-1]
            and self.smi.smi[-1] > 0
        ):
            self.buy(percent=95)
        elif (
            self.position
            and self.fast.valid[-1]
            and self.slow.valid[-1]
            and self.fast[-1] < self.slow[-1]
        ):
            self.position.close()
