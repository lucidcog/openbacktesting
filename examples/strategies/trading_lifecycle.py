"""订单事件、资金拒绝、分批费用及期末清算；每单位费按真实成交收取；复合费用见高级设置教程。

预期：10单位分两次退出，三次成交费用10；资金不足订单拒绝；
末期另买2单位并清算，再收费2，最终余额9988，无剩余仓位。
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
            self.buy(qty=10, sl=90, tp=110, tag={"purpose": "分批退出"})
        elif bar == 3:
            self.trades[0].close(qty=5)
        elif bar == 4:
            self.close_position()
        elif bar == 5:
            self.buy(qty=1000)  # 资金拒绝
            self.buy(qty=30)  # 总暴露限制
            self.sell(qty=1)  # 禁止新增空头
        elif bar == 6:
            self.buy(qty=2)
