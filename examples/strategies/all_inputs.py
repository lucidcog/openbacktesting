"""全部九种 Input：参数声明、枚举选择、颜色、时间与时段的运行值。

使用随包 GOOG 前 120 根日线，无额外依赖；只绘图和记录日志，不下单，不涉及仓位与费用。
作者脚本由宿主执行，运行命令见示例索引。title 是配置键，字段名供 self 访问。
time 是 Unix 毫秒，本例用于控制着色起点；session 只验证并规范化字符串，
本例记录其值，不据此过滤日线，也不提供交易日历或盘中时段判断。
group/inline/display/active/confirm 都是界面提示元数据，不会自行启动或控制界面。
"""

from enum import Enum

from openbacktesting import Strategy, backtest, inputs


class AverageKind(Enum):
    # 配置保存成员名称 "EMA" / "SMA"，不是这里的 .value。
    EMA = "指数均线"
    SMA = "简单均线"


@backtest()
class AllInputs(Strategy):
    highlight = inputs.bool(True, title="显示高亮", group="显示")
    length = inputs.int(20, title="均线周期", minval=2, maxval=100, step=1, group="均线")
    multiplier = inputs.float(
        1.02,
        title="高亮倍率",
        minval=1.0,
        maxval=2.0,
        step=0.01,
        group="显示",
        active={"title": "显示高亮"},
        tooltip="收盘价超过均线乘以此倍率时着色；step 是调整增量，不是整除限制。",
    )
    source = inputs.string(
        "close", title="价格来源", options=["close", "hl2"], group="均线", inline="选择"
    )
    average_kind = inputs.enum(
        AverageKind.EMA,
        title="均线类型",
        options=[AverageKind.EMA, AverageKind.SMA],
        group="均线",
        inline="选择",
    )
    reference_price = inputs.price(
        100.0,
        title="参考价格",
        group="显示",
        confirm=True,
        tooltip="仅绘制水平线；price 不支持 minval/maxval/step/options。",
    )
    start_time = inputs.time(
        1092873600000,
        title="高亮起点",
        group="显示",
        tooltip="2004-08-19 00:00:00 UTC，单位为毫秒。",
    )
    session = inputs.session(
        "24x7",
        title="时段说明",
        display="data_window",
        tooltip="仅展示规范化值，不自动过滤行情；24x7 变为 0000-0000:1234567。",
    )
    line_color = inputs.color("#22aa44", title="均线颜色", group="显示")

    def init(self):
        source = self.close if self.source == "close" else self.hl2
        if self.average_kind is AverageKind.EMA:
            self.average = self.ta.ema(source, length=self.length)
        else:
            self.average = self.ta.sma(source, length=self.length)
        # 运行时为 Enum 和 Color 对象；派生颜色不修改只读的 Input。
        self.background = self.line_color.with_transparency(85)
        self.plotting.line(self.average, title=self.average_kind.value, color=self.line_color)
        self.plotting.level(self.reference_price, title="参考价格")
        self.log.info(f"均线={self.average_kind.name}，时段={self.session}（仅记录，不过滤行情）")

    def next(self):
        if not self.highlight or not self.average.valid[-1]:
            return
        # 示例宿主提供 UTC 索引；不把整数 time 猜测成秒或本地日期。
        current_ms = self.data_index[-1].timestamp() * 1000
        start_ms = self.start_time
        if current_ms < start_ms:
            return
        if self.close[-1] > self.average[-1] * self.multiplier:
            self.plotting.bg_color(self.background)
