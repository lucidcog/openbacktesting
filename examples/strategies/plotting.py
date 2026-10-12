"""Data-only plotting: main/secondary panes, fills, run markers, and per-bar backgrounds/candle colors.

The first 120 bundled GOOG daily bars, with no extra dependencies. Demonstrate a fixed one-unit trade, 0.2% commission, and end-of-run liquidation.
The author declares a strategy; after running it the host calls export_result. Display text as plain text without executing HTML.
"""

from openbacktesting import Color, EndPolicy, Strategy, backtest, colors, inputs


@backtest(commission_value=0.2, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class PlottingDemo(Strategy):
    up_color = inputs.color("#22aa44", title="Rising color")
    down_color = inputs.color(colors.RED, title="Falling color")

    def init(self):
        # String or constant defaults both become Color inside the strategy; derived values do not mutate parameters.
        self.up_background = self.up_color.with_transparency(85)
        self.transparent_up = Color(
            self.up_color.red, self.up_color.green, self.up_color.blue, alpha=0
        )
        ema = self.ta.ema(length=12)
        self.plotting.line(
            ema, color=self.up_color
        )  # Omit id/title/pane: automatic identity, title fallback, and the main pane.
        self.plotting.line(self.close, id="close", title="Close", style="step", color="#708090")
        pane = self.plotting.pane(title="MACD")
        self.macd_pane = pane
        macd = self.ta.macd()
        lower = self.plotting.line(macd.macd, pane=pane, title="MACD")
        upper = self.plotting.line(macd.signal, pane=pane, title="Signal line")
        self.plotting.fill(lower, upper, color=Color.from_hex("#0088ff30"))
        self.plotting.level(0, pane=pane, color=Color.rgb(120, 123, 134))
        self.plotting.histogram(macd.histogram, pane=pane, color=colors.BLUE)
        self.entered = False

    def next(self):
        rising = self.close[-1] > self.open[-1]
        self.plotting.bg_color(self.up_background if rising else None)
        self.plotting.bg_color("#0088ff10", pane=self.macd_pane)
        self.plotting.bar_color(self.up_color if rising else self.down_color)
        if len(self.data) == 60:
            self.plotting.bg_color(None)  # Clear the current bar's main-pane background, leaving other panes and prior bars unchanged.
            self.plotting.bar_color(self.transparent_up)  # Fully transparent is still a color, not None.
        if not self.entered:
            self.entered = True
            self.plotting.marker(
                text="Buy signal", shape="triangle_up", position="below_bar", color=self.up_color
            )
            self.buy(qty=1)
        if len(self.data) == 60:
            self.plotting.marker(anchor_bar=57, text="Confirmed at bar 60, marked at bar 58")
        if len(self.data) == 61:
            self.plotting.bar_color(None)  # Undo the candle override set earlier in this next call.

    def on_fill(self, fill):
        self.plotting.marker(position="price", price=fill.price, text="Fill notification")
