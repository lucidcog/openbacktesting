"""内置 EMA 与 inputs：作者脚本仅声明策略，由框架执行。

数据为随包 GOOG 日线，无额外依赖。快慢周期、整数交易数量和做空开关由 inputs 配置。
EMA 使用 self.ta.ema 的默认 SMA seed，前 length-1 根为空值。
每笔按 0.2% 收取手续费、互斥订单；保留期末未平仓仓位，统计只包含已平仓交易。
"""

from openbacktesting import Strategy, backtest, inputs


@backtest(commission_value=0.2, exclusive_orders=True)
class EmaCross(Strategy):
    fast = inputs.int(12, title="快线周期", minval=1, group="均线")
    slow = inputs.int(26, title="慢线周期", minval=2, group="均线")
    units = inputs.int(1, title="交易数量", minval=1, group="交易")
    short_enabled = inputs.bool(False, title="允许做空", group="交易")

    def init(self):
        if self.fast >= self.slow:
            raise ValueError("快线周期必须小于慢线周期")
        self.fast_line = self.ta.ema(self.close, length=self.fast)
        self.slow_line = self.ta.ema(self.close, length=self.slow)

    def next(self):
        if self.ta.is_crossover(self.fast_line, self.slow_line):
            self.position.close()
            self.buy(qty=self.units)
        elif self.ta.is_crossunder(self.fast_line, self.slow_line):
            self.position.close()
            if self.short_enabled:
                self.sell(qty=self.units)
