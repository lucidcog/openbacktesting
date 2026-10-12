"""三份仓位分三次退出；每份每边费用 1，同收盘成交，净损益分别 10、-4、0。

closed_count 按关闭片段计数；next 提交退出后仍读取成交前快照，on_fill 可见新事实。
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
        assert self.initial.closed_count == 0  # 已保存的快照不随成交改变。
        assert self.final.closed_count == 3
        assert self.final.net_profit == 6
        assert self.final.win_rate == 1 / 3
