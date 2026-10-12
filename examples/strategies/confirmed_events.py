"""确认事件与月锚点：进阶作者脚本，组合、形态及周期水平共用 self.ta。

随包 GOOG 日线、无额外依赖。左右各三根的 Pivot 只在右侧确认后可见，不能回填交易。
PeriodStart 标记每月首根输入 bar；首月可能不完整，生产数据须保证周期完整性。
互斥订单、期末平仓，手续费沿用默认零；此例展示机制，不提供收益验证。
"""

from openbacktesting import EndPolicy, Strategy, backtest


@backtest(exclusive_orders=True, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class ExpandedSignals(Strategy):
    def init(self):
        self.fast = self.ta.ema(self.close, length=10)
        self.slow = self.ta.ema(self.close, length=30)
        self.cross = self.ta.crossover(self.fast, self.slow)
        self.smi = self.ta.smi_stochastic()
        self.pivot = self.ta.pivothigh(left=3, right=3)
        self.pattern = self.ta.cdl_engulfing()
        self.levels = self.ta.pivot_points(inputs={"anchor": "PeriodStart"}, method="traditional")

    def next(self):
        bullish = self.pattern.valid[-1] and self.pattern[-1] > 0
        if (
            self.cross.valid[-1]
            and self.cross[-1]
            and bullish
            and self.smi.smi.valid[-1]
            and self.smi.smi[-1] > 0
        ):
            self.buy(percent=95)
        elif (
            self.position
            and self.fast.valid[-1]
            and self.slow.valid[-1]
            and self.fast[-1] < self.slow[-1]
        ):
            self.position.close()
