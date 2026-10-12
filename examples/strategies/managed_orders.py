"""Expiry, atomic mixed-size entry OCO, protection groups, and percentage trailing stops; slippage is 0.5 per fill.

Same-bar dual-trigger OCO follows submission order and records ambiguity; trailing prices update at close and take effect on the next bar.
This deterministic OHLC policy cannot establish the actual intrabar path.
"""

import pandas as pd

from openbacktesting import SlippageType, Strategy, backtest
from openbacktesting.broker import OrderRequest


@backtest(slippage_type=SlippageType.FIXED, slippage_value=0.5)
class ManagedOrders(Strategy):
    def init(self):
        self.reference = self.ta.sma(self.close, length=2)
        # Record intent only here; convert on submission using the same account and Close.
        self.long_entry = OrderRequest(side="buy", percent=1, stop=105, sl=90, tp=130)
        self.short_entry = OrderRequest(side="sell", amount=100, stop=95)

    def next(self):
        bar = len(self.data) - 1
        if bar == 2:
            self.buy(qty=1, limit=80, valid_bars=1)
            self.buy(qty=1, limit=80, expires_at=self.data_index[-1] + pd.Timedelta(days=1))
        elif bar == 3:
            self.entries = self.submit_oco(
                first=self.long_entry,
                second=self.short_entry,
            )
        elif bar == 4:
            self.trades[0].set_trailing_stop(amount=10)
            self.trades[0].set_trailing_stop(percent=0.1)
