"""Three units exit in three fills; each unit costs 1 per side, fills occur on the same close, and net P&L is 10, -4, and 0.

closed_count counts closed portions; next still reads the pre-fill snapshot after submitting an exit, while on_fill sees the new facts.
"""

from openbacktesting import CommissionType, ExecutionTiming, Strategy, backtest


@backtest(
    commission_type=CommissionType.CASH_PER_CONTRACT,
    commission_value=1,
    execution_timing=ExecutionTiming.SAME_CLOSE,
)
class ClosedTradeStatistics(Strategy):
    def init(self):
        self.reference = self.ta.sma(self.close, length=1)
        self.initial = self.closed_trade_stats
        self.snapshots = []
        self.fill_snapshots = []

    def next(self):
        bar = self.bar_index
        if self.reference.valid[-1]:
            if bar == 0:
                self.buy(qty=3)
            elif bar in (1, 2, 3):
                self.trades[0].close(qty=1)
        self.snapshots.append(self.closed_trade_stats)

    def on_fill(self, fill):
        self.fill_snapshots.append(self.closed_trade_stats)

    def on_finish(self, summary):
        self.final = self.closed_trade_stats
        assert self.initial.closed_count == 0  # Saved snapshots do not change after fills.
        assert self.final.closed_count == 3
        assert self.final.net_profit == 6
        assert self.final.win_rate == 1 / 3
