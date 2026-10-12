"""纯数据绘图：主副图、填充、运行标记与逐 bar 背景/K 线颜色。

随包 GOOG 前 120 根日线，无额外依赖。固定一单位演示交易，手续费 0.2%，期末平仓。
作者仅声明策略；宿主运行后 export_result，文本作为纯文本展示，不执行 HTML。
"""

from openbacktesting import Color, EndPolicy, Strategy, backtest, colors, inputs


@backtest(commission_value=0.2, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class PlottingDemo(Strategy):
    up_color = inputs.color("#22aa44", title="上涨颜色")
    down_color = inputs.color(colors.RED, title="下跌颜色")

    def init(self):
        # 字符串或常量默认值在策略内都成为 Color；派生值不修改参数。
        self.up_background = self.up_color.with_transparency(85)
        self.transparent_up = Color(
            self.up_color.red, self.up_color.green, self.up_color.blue, alpha=0
        )
        ema = self.ta.ema(length=12)
        self.plotting.line(
            ema, color=self.up_color
        )  # id/title/pane 全部省略：自动身份、标题回退、主图。
        self.plotting.line(self.close, id="close", title="收盘", style="step", color="#708090")
        pane = self.plotting.pane(title="MACD")
        self.macd_pane = pane
        macd = self.ta.macd()
        lower = self.plotting.line(macd.macd, pane=pane, title="MACD")
        upper = self.plotting.line(macd.signal, pane=pane, title="信号线")
        self.plotting.fill(lower, upper, color=Color.from_hex("#0088ff30"))
        self.plotting.level(0, pane=pane, color=Color.rgb(120, 123, 134))
        self.plotting.histogram(macd.histogram, pane=pane, color=colors.BLUE)
        self.entered = False

    def next(self):
        rising = self.close[-1] > self.open[-1]
        self.plotting.bg_color(self.up_background if rising else None)
        self.plotting.bg_color("#0088ff10", pane=self.macd_pane)
        self.plotting.bar_color(self.up_color if rising else self.down_color)
        if len(self.data) == 60:
            self.plotting.bg_color(None)  # 清除当根主图背景，不清除副图或旧 bar。
            self.plotting.bar_color(self.transparent_up)  # 全透明仍是颜色，不等于 None。
        if not self.entered:
            self.entered = True
            self.plotting.marker(
                text="买入信号", shape="triangle_up", position="below_bar", color=self.up_color
            )
            self.buy(qty=1)
        if len(self.data) == 60:
            self.plotting.marker(anchor_bar=57, text="第 60 根确认，回标第 58 根")
        if len(self.data) == 61:
            self.plotting.bar_color(None)  # 撤销本次 next 较早设置的 K 线覆盖。

    def on_fill(self, fill):
        self.plotting.marker(position="price", price=fill.price, text="成交通知")
