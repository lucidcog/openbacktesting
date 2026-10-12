"""Execute from the first bar: data boundaries, integer positions, labels, and local validity guards.

Bundled GOOG daily data, with no extra dependencies. Log and color only; no orders, fees, or sizing.
Boundary states describe fixed input data and do not indicate live market hours or run success.
"""

from openbacktesting import Strategy, backtest, colors


@backtest()
class BarStates(Strategy):
    def init(self):
        self.average = self.ta.sma(self.close, length=3)
        self.observed = []
        self.above_average = []
        self.plotting.line(self.average, title="Three-bar moving average")

    def next(self):
        # Frozen snapshots can be saved; data_index is a label and bar_index is a zero-based position.
        state = self.bar_state
        self.observed.append((self.bar_index, self.data_index[-1], state))
        if state.is_first:
            self.plotting.bg_color(colors.BLUE)
        if state.is_last:
            self.plotting.bar_color(colors.ORANGE)
        # Guard only logic that depends on the moving average; first-bar logging and coloring above still run before it is ready.
        if self.average.valid[-1]:
            self.above_average.append(self.close[-1] > self.average[-1])
