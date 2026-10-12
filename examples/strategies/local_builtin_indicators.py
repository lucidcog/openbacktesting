"""Eight local indicator extensions; the host supplies causal anchors and discrete observations through Reset/Regime. No orders.

Sources use column names or handles from the same chart; check valid per output channel and do not pass pandas Series directly.
"""

from openbacktesting import Strategy, backtest


@backtest()
class LocalBuiltinIndicators(Strategy):
    def init(self):
        self.range_fallback = self.ta.true_range(handle_na=True)
        inputs = {"source": self.close, "volume": self.volume, "anchor": "Reset"}
        self.weighted = self.ta.anchored_vwap(inputs=inputs)
        self.bands = self.ta.anchored_vwap_bands(inputs=inputs, stdev_mult=1.0)
        self.regime = self.ta.mode("Regime", length=3)
        self.channel = self.ta.kc(length=3, use_true_range=False)
        self.floored = self.ta.alma(self.close, length=3, floor=True)
        self.fit = self.ta.linreg(self.close, length=3, offset=1)
        self.levels = self.ta.pivot_points(inputs={"anchor": "Reset"}, developing=True)
        self.observed = []
        self.plotting.line(self.weighted, title="Conditional VWAP")
        self.plotting.line(self.bands.upper, title="Weighted population-standard-deviation upper band")

    def next(self):
        handles = (
            self.range_fallback,
            self.weighted,
            self.bands.vwap,
            self.bands.lower,
            self.bands.upper,
            self.regime,
            self.channel.middle,
            self.floored,
            self.fit,
            self.levels.p,
        )
        self.observed.append(tuple(float(h[-1]) if h.valid[-1] else None for h in handles))
