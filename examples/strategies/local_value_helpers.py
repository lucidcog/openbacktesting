"""Explicit tick rounding and per-bar gradients; the host injects a 0.05 tick, with no commission, a one-unit market buy, and end-of-run liquidation.

Rounded candidate prices still pass instrument.price validation; gradients use existing color-event export.
"""

from openbacktesting import Color, EndPolicy, Strategy, backtest, colors


@backtest(end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class LocalValueHelpers(Strategy):
    def init(self):
        self.average = self.ta.sma(self.close, length=2)
        self.rounded = self.instrument.round_price_to_tick(100.025)
        assert self.instrument.price(self.rounded) == 100.05
        self.emitted = []

    def next(self):
        if not self.average.valid[-1]:
            return
        value = float(self.close[-1] - self.average[-1])
        shade = Color.from_gradient(
            value, lower=-1, upper=1, lower_color=colors.RED, upper_color=colors.GREEN
        )
        self.plotting.bar_color(shade)
        self.plotting.bg_color(shade.with_transparency(80))
        self.emitted.append(shade)
        bar = self.bar_index
        if bar == 1:
            pending = self.buy(qty=1, limit=self.rounded)
            pending.cancel()  # A valid grid price passes existing validation; cancel it and submit a market order.
            self.buy(qty=1)
