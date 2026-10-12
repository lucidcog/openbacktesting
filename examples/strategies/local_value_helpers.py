"""显式 tick 舍入和逐根渐变；宿主注入 0.05 tick，无手续费，市价买一份后期末平仓。

舍入候选价仍须通过 instrument.price；渐变沿用既有颜色事件导出。
"""

from openbacktesting import Color, EndPolicy, Strategy, backtest, colors


@backtest(end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class LocalValueHelpers(Strategy):
    def init(self):
        self.average = self.ta.sma(self.close, length=2)
        self.rounded = self.instrument.round_price_to_tick(100.025)
        assert self.instrument.price(self.rounded) == 100.05
        self.emitted = []

    def next(self):
        if not self.average.valid[-1]:
            return
        value = float(self.close[-1] - self.average[-1])
        shade = Color.from_gradient(
            value, lower=-1, upper=1, lower_color=colors.RED, upper_color=colors.GREEN
        )
        self.plotting.bar_color(shade)
        self.plotting.bg_color(shade.with_transparency(80))
        self.emitted.append(shade)
        bar = self.bar_index
        if bar == 1:
            pending = self.buy(qty=1, limit=self.rounded)
            pending.cancel()  # 合法网格价通过原校验；取消后另下市价单。
            self.buy(qty=1)
