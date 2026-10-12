"""Balance, actual fees, and position snapshots independent of strategies and result tables."""

from openbacktesting.broker.models import AccountSnapshot, PositionSnapshot


class TradingLedger:
    """Record only actual executions; candidate calculations must not call apply."""

    def __init__(self, balance):
        self.initial_balance = float(balance)
        self.balance = float(balance)
        self.realized_pnl_gross = 0.0
        self.fees_paid = 0.0

    def apply(self, realized_pnl_gross, fee):
        self.realized_pnl_gross += realized_pnl_gross
        self.fees_paid += fee
        self.balance = self.initial_balance + self.realized_pnl_gross - self.fees_paid

    def position(self, trades, price):
        long_qty = sum(t.size for t in trades if t.size > 0)
        short_qty = sum(-t.size for t in trades if t.size < 0)
        long_cost = sum(t.size * t.entry_price for t in trades if t.size > 0)
        short_cost = sum(-t.size * t.entry_price for t in trades if t.size < 0)
        long_avg = long_cost / long_qty if long_qty else None
        short_avg = short_cost / short_qty if short_qty else None
        average = None if long_qty and short_qty else long_avg or short_avg
        gross_pl = sum(t.size * (price - t.entry_price) for t in trades)
        fees = sum(t._entry_commission for t in trades)
        cost = long_cost + short_cost
        return PositionSnapshot(
            long_qty - short_qty,
            long_qty + short_qty,
            long_qty,
            short_qty,
            long_avg,
            short_avg,
            average,
            (long_qty + short_qty) * price,
            (long_qty - short_qty) * price,
            gross_pl,
            gross_pl - fees,
            fees,
            (gross_pl - fees) / cost if cost and average is not None else None,
        )

    def account(self, position, margin):
        equity = self.balance + position.unrealized_pnl_gross
        used = position.gross_notional * margin
        return AccountSnapshot(
            self.balance,
            equity,
            self.realized_pnl_gross,
            position.unrealized_pnl_gross,
            self.fees_paid,
            used,
            max(0.0, equity - used),
            position.gross_notional,
            position.net_notional,
        )
