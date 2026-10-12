"""EMA 与 MACD 过滤：推荐作者脚本，框架从当前图表注入数据并运行。

随包 GOOG 日线、无额外依赖；均线周期由 inputs 调整。内置指标统一通过 self.ta 在 init 登记，next 只取当前标量。
手续费 0.2%、互斥订单，期末平仓计入统计；默认下单规模沿用引擎可用资金比例。
"""

from openbacktesting import EndPolicy, Strategy, backtest, inputs


@backtest(commission_value=0.2, exclusive_orders=True, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class BuiltInSignals(Strategy):
    length = inputs.int(20, minval=2, title="均线周期")

    def init(self):
        self.ema = self.ta.ema(self.close, length=self.length)
        self.macd = self.ta.macd(self.close)

    def next(self):
        # 交叉需要两根有效均线；MACD 过滤只用于入场。
        if len(self.close) < 2 or not self.ema.valid[-2:].all():
            return
        if (
            self.close[-2] < self.ema[-2]
            and self.close[-1] > self.ema[-1]
            and self.macd.histogram.valid[-1]
            and self.macd.histogram[-1] > 0
        ):
            self.buy(percent=95)
        elif self.ema[-2] < self.close[-2] and self.ema[-1] > self.close[-1]:
            self.position.close()
