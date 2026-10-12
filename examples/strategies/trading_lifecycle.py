"""Order events, insufficient-funds rejection, partial-exit fees, and end-of-run liquidation; per-unit fees use actual fills. See the advanced settings tutorial for composite fees.

Expected: exit 10 units in two portions, with fees of 10 across three fills; reject an insufficient-funds order;
Buy and liquidate another 2 units at the end, charging 2 more; final balance is 9988 with no remaining position.
"""

from openbacktesting import CommissionType, EndPolicy, Strategy, backtest


@backtest(
    commission_type=CommissionType.CASH_PER_CONTRACT,
    commission_value=0.5,
    allow_short=False,
    max_gross_exposure=0.2,
    end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE,
)
class TradingLifecycle(Strategy):
    def init(self):
        self.reference = self.ta.sma(self.close, length=2)
        self.events = []
        self.fill_events = []
        self.snapshots = []

    def on_start(self):
        self.initial_account = self.account

    def on_fill(self, fill):
        self.fill_events.append(fill)

    def on_order(self, event):
        self.events.append(event)

    def on_finish(self, summary):
        self.summary = summary
        assert summary.account.fees_paid == sum(fill.fee for fill in self.fill_events)

    def next(self):
        bar = len(self.data) - 1
        self.snapshots.append((self.account, self.position.snapshot))
        if bar == 2:
            self.buy(qty=10, sl=90, tp=110, tag={"purpose": "Partial exits"})
        elif bar == 3:
            self.trades[0].close(qty=5)
        elif bar == 4:
            self.close_position()
        elif bar == 5:
            self.buy(qty=1000)  # Insufficient-funds rejection
            self.buy(qty=30)  # Total exposure limit
            self.sell(qty=1)  # Prohibit new shorts
        elif bar == 6:
            self.buy(qty=2)
