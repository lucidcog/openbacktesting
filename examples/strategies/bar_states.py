"""首根逐根执行：数据首尾、整数位置、标签及局部有效性防护。

随包 GOOG 日线，无额外依赖。只记录与着色，不下单；手续费和仓位不参与示例。
首尾状态针对固定输入，不能作为实时市场开闭或运行成功的判断。
"""

from openbacktesting import Strategy, backtest, colors


@backtest()
class BarStates(Strategy):
    def init(self):
        self.average = self.ta.sma(self.close, length=3)
        self.observed = []
        self.above_average = []
        self.plotting.line(self.average, title="三根均线")

    def next(self):
        # 冻结快照适合保存；data_index 是标签，bar_index 是零起点位置。
        state = self.bar_state
        self.observed.append((self.bar_index, self.data_index[-1], state))
        if state.is_first:
            self.plotting.bg_color(colors.BLUE)
        if state.is_last:
            self.plotting.bar_color(colors.ORANGE)
        # 只保护依赖均线的逻辑，均线未就绪时仍执行上方的首根记录与着色。
        if self.average.valid[-1]:
            self.above_average.append(self.close[-1] > self.average[-1])
