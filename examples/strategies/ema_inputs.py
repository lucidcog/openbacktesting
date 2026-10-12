"""Built-in EMA and inputs: the author script declares the strategy and the framework executes it.

Bundled GOOG daily data, with no extra dependencies. inputs configures fast/slow periods, integer trade quantity, and the shorting switch.
EMA uses the default SMA seed from self.ta.ema; the first length-1 bars are missing.
0.2% commission per trade and exclusive orders; retain open positions at the end, with statistics counting closed trades only.
"""

from openbacktesting import Strategy, backtest, inputs


@backtest(commission_value=0.2, exclusive_orders=True)
class EmaCross(Strategy):
    fast = inputs.int(12, title="Fast period", minval=1, group="Moving average")
    slow = inputs.int(26, title="Slow period", minval=2, group="Moving average")
    units = inputs.int(1, title="Trade quantity", minval=1, group="Trades")
    short_enabled = inputs.bool(False, title="Allow shorting", group="Trades")

    def init(self):
        if self.fast >= self.slow:
            raise ValueError("Fast period must be less than slow period")
        self.fast_line = self.ta.ema(self.close, length=self.fast)
        self.slow_line = self.ta.ema(self.close, length=self.slow)

    def next(self):
        if self.ta.is_crossover(self.fast_line, self.slow_line):
            self.position.close()
            self.buy(qty=self.units)
        elif self.ta.is_crossunder(self.fast_line, self.slow_line):
            self.position.close()
            if self.short_enabled:
                self.sell(qty=self.units)
