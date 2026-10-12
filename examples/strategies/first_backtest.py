"""First backtest: buy when price crosses above EMA and close below it; declare the strategy only.

Bundled GOOG daily data, 0.2% commission, and exclusive orders; end-of-run liquidation enters the results.
"""

from openbacktesting import EndPolicy, Strategy, backtest


@backtest(commission_value=0.2, exclusive_orders=True, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class FirstBacktest(Strategy):
    def init(self):
        self.average = self.ta.ema(self.close, length=20)

    def next(self):
        if self.ta.is_crossover(self.close, self.average):
            self.buy(percent=95)
        elif self.ta.is_crossunder(self.close, self.average):
            self.position.close()
