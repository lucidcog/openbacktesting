"""稳定行情来源：保存引用、派生价格组合和逐 bar 标量读取。

随包 GOOG 日线，无额外依赖；此作者脚本仅声明策略。均线周期由 inputs 配置。
hlcc4 = (H + L + 2C) / 4，八个来源均为只读句柄，保存引用仍随游标推进。
data_index/df 每次读取返回当前可见范围，保存的 pandas 对象不会自动更新；pip 是价格精度标量。
策略仅演示用法：每次一股、手续费 0.2%、互斥订单并在期末平仓，不代表收益有效。
"""

from openbacktesting import EndPolicy, Strategy, backtest, inputs


@backtest(commission_value=0.2, exclusive_orders=True, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class DataSources(Strategy):
    length = inputs.int(20, title="平滑周期", minval=2)

    def init(self):
        self.saved_close = self.close
        self.smoothed = self.ta.ema(self.hlcc4, length=self.length)

    def next(self):
        # 保存的来源与直接访问的来源都只显示当前前缀；[-1] 是当前 bar。
        rising = self.saved_close[-1] > self.open[-1]
        liquid = self.volume[-1] > 0
        inside_range = self.low[-1] <= self.hl2[-1] <= self.high[-1]
        above_average = self.smoothed.valid[-1] and self.hlc3[-1] > self.smoothed[-1]
        if not self.position and rising and liquid and inside_range and above_average:
            self.buy(qty=1)
        elif self.position and self.smoothed.valid[-1] and self.saved_close[-1] < self.smoothed[-1]:
            self.position.close()
