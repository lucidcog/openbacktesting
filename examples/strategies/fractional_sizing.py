"""三种下单规模、原生0.001数量步长、预算计算、目标去重与只减仓；价格始终是100。

预期成交数量0.1、0.1、0.2；10份资产退出请求只能减掉实际0.2份。
金额与百分数示例挂单展示显式覆盖默认量，随后撤单；规模快照保留提交时的预算。
止损预算只是计划损失，不能限制跳空损失。
宿主可覆盖为 default_qty_type=QuantityType.PERCENT_OF_EQUITY、default_qty_value=0.1，同样先买0.1份。
过小默认预算会在提交前报错；完整运行与拒绝示例见 advanced/strategy_settings.py。
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
            assert self.invalid_noop_rejected  # 无需下单也会校验条件。
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
            assert reference_price == 100  # 按 Close，不按 limit。
            self.amount_order.cancel()
            self.percent_order.cancel()
            self.buy()  # 省略数量使用声明；下方只减仓始终显式给出数量。
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
