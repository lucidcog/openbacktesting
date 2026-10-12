"""Record three log levels and the current bar; the host retrieves timestamps and source locations.

Host-provided historical data, with no extra dependencies or orders; positions and fees do not apply.
error only records a level; enable the "Demonstrate failure" parameter to raise an explicit exception.
"""

from openbacktesting import Strategy, backtest, inputs


@backtest()
class StrategyLogs(Strategy):
    fail = inputs.bool(False, title="Demonstrate failure")

    def init(self):
        # Initialization logs have no current bar but still record system time and the actual calling source line.
        self.average = self.ta.sma(self.close, length=3)
        self.log.info("Initialization complete")

    def next(self):
        self.log.info(
            f"bar={self.bar_index}, close={self.close[-1]:.2f}, sma={self.average[-1]:.2f}"
        )
        if self.bar_state.is_first:
            self.log.warning("The first bar has no previous price")
            self.log.error("Demonstrate error level; backtest continues")
            if self.fail:
                raise ValueError("Demonstrate explicit failure")

    def on_finish(self, summary):
        self.log.info(f"End reason: {summary.reason}")
