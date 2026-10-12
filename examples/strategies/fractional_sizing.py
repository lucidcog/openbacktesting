"""Three sizing modes, native 0.001 quantity steps, budgets, target deduplication, and reduce-only orders; price is always 100.

Expected fill quantities are 0.1, 0.1, and 0.2; an exit request for 10 units can reduce only the actual 0.2 units.
Cash and percentage pending orders demonstrate explicit default-quantity overrides before cancellation; sizing snapshots retain submission budgets.
A stop-loss budget is planned loss only and cannot limit gap losses.
The host can override default_qty_type=QuantityType.PERCENT_OF_EQUITY and default_qty_value=0.1, still initially buying 0.1 units.
An undersized default budget fails before submission; see advanced/strategy_settings.py for complete runs and rejection examples.
"""

from openbacktesting import QuantityType, Strategy, backtest
from openbacktesting.strategy.sizing import equity_fraction, fixed_quantity, stop_risk


@backtest(default_qty_type=QuantityType.FIXED, default_qty_value=0.1)
class FractionalSizing(Strategy):
    def init(self):
        self.reference = self.ta.sma(self.close, length=2)
        self.invalid_noop_rejected = False

    def next(self):
        bar = len(self.data) - 1
        if bar == 0:
            assert self.order_target_quantity(target=0) is None
            try:
                self.order_target_quantity(target=0, limit=-1)
            except ValueError:
                self.invalid_noop_rejected = True
            assert self.invalid_noop_rejected  # Validate conditions even without submitting an order.
        elif bar == 2:
            self.risk_budget = stop_risk(
                0.01,
                account=self.account,
                reference_price=self.close[-1],
                stop_price=95,
                instrument=self.instrument,
            )
            self.notional_budget = equity_fraction(
                0.1,
                account=self.account,
                reference_price=self.close[-1],
                instrument=self.instrument,
            )
            decision = fixed_quantity(
                0.1, reference_price=self.close[-1], instrument=self.instrument
            )
            quantity = decision.qty
            assert quantity == 0.1
            self.amount_order = self.buy(amount=20, limit=80)
            self.percent_order = self.buy(percent=0.2, limit=80)
            amount_qty = self.amount_order.sizing.qty
            percent_qty = self.percent_order.sizing.qty
            reference_price = self.amount_order.sizing.reference_price
            assert amount_qty == percent_qty == 0.2
            assert reference_price == 100  # Use Close, not limit.
            self.amount_order.cancel()
            self.percent_order.cancel()
            self.buy()  # Omitted quantity uses the declaration; reduce-only orders below always specify quantity explicitly.
        elif bar == 3:
            self.pending = self.order_target_quantity(target=0.3, limit=80)
        elif bar == 4:
            existing = self.pending
            assert self.order_target_quantity(target=0.3, limit=80) is existing
        elif bar == 5:
            target = self.order_target_value(target=20)
            assert self.order_target_percent(target=0.002) is target
        elif bar == 6:
            self.sell(qty=10, reduce_only=True)
