"""第一次回测：价格上穿 EMA 时买入，下穿时平仓，仅声明策略。

使用随包 GOOG 日线，手续费 0.2%，互斥订单，期末平仓计入结果。
"""

from openbacktesting import EndPolicy, Strategy, backtest


@backtest(commission_value=0.2, exclusive_orders=True, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class FirstBacktest(Strategy):
    def init(self):
        self.average = self.ta.ema(self.close, length=20)

    def next(self):
        if self.ta.is_crossover(self.close, self.average):
            self.buy(percent=95)
        elif self.ta.is_crossunder(self.close, self.average):
            self.position.close()
