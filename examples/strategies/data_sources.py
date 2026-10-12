"""Stable market-data sources: saved references, derived price combinations, and per-bar scalar reads.

Bundled GOOG daily data, with no extra dependencies; this author script only declares a strategy. inputs configures the moving-average period.
hlcc4 = (H + L + 2C) / 4; all eight sources are read-only handles whose saved references follow the cursor.
data_index/df returns the currently visible range on each read; saved pandas objects do not update automatically. pip is a price-precision scalar.
Demonstrate usage only: one share per order, 0.2% commission, exclusive orders, and end-of-run liquidation do not establish valid returns.
"""

from openbacktesting import EndPolicy, Strategy, backtest, inputs


@backtest(commission_value=0.2, exclusive_orders=True, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class DataSources(Strategy):
    length = inputs.int(20, title="Smoothing period", minval=2)

    def init(self):
        self.saved_close = self.close
        self.smoothed = self.ta.ema(self.hlcc4, length=self.length)

    def next(self):
        # Saved and directly accessed sources expose only the current prefix; [-1] is the current bar.
        rising = self.saved_close[-1] > self.open[-1]
        liquid = self.volume[-1] > 0
        inside_range = self.low[-1] <= self.hl2[-1] <= self.high[-1]
        above_average = self.smoothed.valid[-1] and self.hlc3[-1] > self.smoothed[-1]
        if not self.position and rising and liquid and inside_range and above_average:
            self.buy(qty=1)
        elif self.position and self.smoothed.valid[-1] and self.saved_close[-1] < self.smoothed[-1]:
            self.position.close()
