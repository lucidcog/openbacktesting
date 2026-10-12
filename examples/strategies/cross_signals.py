"""交叉序列与即时布尔判断：序列用于事件组合，is_* 用于当前 bar 下单。

随包 GOOG 日线，无额外依赖。前一根相等后分离也算交叉。
互斥订单、期末平仓、默认零手续费；示例只展示 API，不验证策略收益。
"""

from openbacktesting import EndPolicy, Strategy, backtest


@backtest(exclusive_orders=True, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class CrossSignals(Strategy):
    def init(self):
        self.fast = self.ta.ema(self.close, length=10)
        self.slow = self.ta.ema(self.close, length=30)
        self.crosses = self.ta.cross(self.fast, self.slow)
        self.up = self.ta.crossover(self.fast, self.slow)
        self.down = self.ta.crossunder(self.fast, self.slow)
        # 序列可继续组合：离上次交叉的根数、上次上穿/下穿时的价格。
        self.cross_age = self.ta.barssince(self.crosses)
        self.last_up_price = self.ta.valuewhen(self.up, self.close)
        self.last_down_price = self.ta.valuewhen(self.down, self.close)

    def next(self):
        # 即时判断不登记新指标；返回原生 bool，直接用于条件分支。
        if self.ta.is_cross(self.fast, self.slow):
            if self.ta.is_crossover(self.fast, self.slow):
                self.buy(percent=95)
            elif self.ta.is_crossunder(self.fast, self.slow):
                self.position.close()
