"""EMA with a MACD filter: recommended author script; the framework injects current chart data and runs it.

Bundled GOOG daily data, with no extra dependencies; inputs adjusts moving-average periods. Register built-ins through self.ta in init; next reads current scalars only.
0.2% commission and exclusive orders; end-of-run liquidation enters statistics. Default sizing follows the engine's available-funds fraction.
"""

from openbacktesting import EndPolicy, Strategy, backtest, inputs


@backtest(commission_value=0.2, exclusive_orders=True, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class BuiltInSignals(Strategy):
    length = inputs.int(20, minval=2, title="Moving-average period")

    def init(self):
        self.ema = self.ta.ema(self.close, length=self.length)
        self.macd = self.ta.macd(self.close)

    def next(self):
        # Crossovers need two valid moving-average bars; the MACD filter applies to entry only.
        if len(self.close) < 2 or not self.ema.valid[-2:].all():
            return
        if (
            self.close[-2] < self.ema[-2]
            and self.close[-1] > self.ema[-1]
            and self.macd.histogram.valid[-1]
            and self.macd.histogram[-1] > 0
        ):
            self.buy(percent=95)
        elif self.ema[-2] < self.close[-2] and self.ema[-1] > self.close[-1]:
            self.position.close()
