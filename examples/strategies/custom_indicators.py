"""自定义指标复用：纯函数、两组参数、具名多输出和 ta 组合。

使用随包 GOOG 前 120 根日线，无额外依赖。百分比通道上下各偏离均线 width，
不是布林带；函数可移入普通 Python 模块，供其他策略导入。
作者脚本仅声明策略；next 读取信号而不下单，因此手续费设为 0，不产生仓位或收益证据。
ind 在 init 批量计算且每次登记重新执行，作者负责因果性；保存句柄而非完整数组。
"""

from typing import NamedTuple

import pandas as pd
from openbacktesting import Strategy, backtest, inputs
from openbacktesting.indicators.types import IndicatorHandle


def mean_band(close: pd.Series, length: int, *, width: float = 0.02) -> pd.DataFrame:
    """返回保留行情索引的均线百分比通道，可脱离策略直接调用。"""
    if isinstance(length, bool) or not isinstance(length, int) or length < 1:
        raise ValueError("length 必须是正整数")
    if isinstance(width, bool) or not isinstance(width, (int, float)) or not 0 <= width <= 1:
        raise ValueError("width 必须在 0 到 1 之间")
    middle = close.rolling(length, min_periods=length).mean()
    return pd.DataFrame(
        {"middle": middle, "upper": middle * (1 + width), "lower": middle * (1 - width)},
        index=close.index,
    )


class TrendLines(NamedTuple):
    """只保存当前运行的指标句柄，不承担计算或更新生命周期。"""

    fast: IndicatorHandle
    slow: IndicatorHandle
    cross: IndicatorHandle


def trend_lines(ta, source, *, fast=5, slow=20) -> TrendLines:
    """在 init 中组合已有指标，保留每条线的有效性和游标。"""
    if fast >= slow:
        raise ValueError("fast 必须小于 slow")
    fast_line = ta.ema(source, length=fast)
    slow_line = ta.ema(source, length=slow)
    return TrendLines(fast_line, slow_line, ta.crossover(fast_line, slow_line))


@backtest(commission_value=0)
class CustomIndicators(Strategy):
    fast_length = inputs.int(5, title="快通道周期", minval=1)
    slow_length = inputs.int(20, title="慢通道周期", minval=1)

    def init(self):
        # .s 是供本次纯计算使用的完整输入快照；登记后保存的是动态句柄。
        self.fast = self.ind(
            mean_band,
            self.close.s,
            self.fast_length,
            width=0.02,
            name=["middle", "upper", "lower"],
        )
        self.slow = self.ind(
            mean_band,
            self.close.s,
            self.slow_length,
            width=0.04,
            name=["middle", "upper", "lower"],
        )
        self.smoothed = self.ta.ema(self.fast["middle"], length=3)
        self.short_trend = trend_lines(self.ta, self.close, fast=5, slow=20)
        self.long_trend = trend_lines(self.ta, self.hlc3, fast=10, slow=30)
        self.plotting.line(self.fast["middle"], title="快通道中线")
        self.plotting.line(self.slow["middle"], title="慢通道中线")

    def next(self):
        self.above = bool(
            self.fast["middle"].valid[-1]
            and self.slow["middle"].valid[-1]
            and self.fast["middle"][-1] > self.slow["middle"][-1]
        )
        self.crossed = bool(self.short_trend.cross.valid[-1] and self.short_trend.cross[-1])


class AnotherStrategy(Strategy):
    """同一计算定义可以在其他策略中使用不同来源和参数。"""

    def init(self):
        self.band = self.ind(mean_band, self.hlc3.s, 10, name=["middle", "upper", "lower"])

    def next(self):
        self.above = bool(self.band["upper"].valid[-1] and self.close[-1] > self.band["upper"][-1])
