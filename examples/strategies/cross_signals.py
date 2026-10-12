"""Crossover series and immediate boolean checks: use series for event composition and is_* for orders on the current bar.

Bundled GOOG daily data, with no extra dependencies. Separation after equality on the previous bar also counts as a crossover.
Exclusive orders, end-of-run liquidation, and default zero commission; this demonstrates the API rather than validating returns.
"""

from openbacktesting import EndPolicy, Strategy, backtest


@backtest(exclusive_orders=True, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class CrossSignals(Strategy):
    def init(self):
        self.fast = self.ta.ema(self.close, length=10)
        self.slow = self.ta.ema(self.close, length=30)
        self.crosses = self.ta.cross(self.fast, self.slow)
        self.up = self.ta.crossover(self.fast, self.slow)
        self.down = self.ta.crossunder(self.fast, self.slow)
        # Series compose further: bars since the last crossover and prices at the last upward/downward cross.
        self.cross_age = self.ta.barssince(self.crosses)
        self.last_up_price = self.ta.valuewhen(self.up, self.close)
        self.last_down_price = self.ta.valuewhen(self.down, self.close)

    def next(self):
        # Immediate checks register no new indicator; they return native bool values for conditional branches.
        if self.ta.is_cross(self.fast, self.slow):
            if self.ta.is_crossover(self.fast, self.slow):
                self.buy(percent=95)
            elif self.ta.is_crossunder(self.fast, self.slow):
                self.position.close()
