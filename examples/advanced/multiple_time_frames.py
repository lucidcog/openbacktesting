"""日/周 RSI 重采样：先理解原生回测与 pandas 日期索引，再显式执行 main。

随包 GOOG 日线，无额外依赖；d_rsi/w_rsi 是日/周周期，level 是入场阈值。
W-FRI 使用周五右标签、完成周期结果再向前填充到日线；数据须有序且日历一致。
GOOG 索引无时区，不处理盘中交易所时区或缺失交易日，不能宣称 Pine 多周期等价。
使用内置 RSI 与均线过滤，手续费 0.2%、止损 8%，不强制期末平仓；输出一次回测统计。
"""

from openbacktesting import Backtest, Strategy
from openbacktesting.indicators import compute
from openbacktesting.lib import resample_apply
from openbacktesting.test import GOOG


def resampled_rsi(close, length):
    """周线使用独立日期索引，通过公开 compute 调用同一内置 RSI。

    self.ta 绑定主回测日历，不能直接登记不同长度的周线；
    resample_apply 负责把计算结果对齐日线并登记为随游标可见的指标。
    """
    return compute("ta.rsi", close.to_frame("Close"), parameters={"length": length}).s


class System(Strategy):
    d_rsi = 30
    w_rsi = 30
    level = 70

    def init(self):
        self.ma10 = self.ta.sma(self.close, length=10)
        self.ma20 = self.ta.sma(self.close, length=20)
        self.ma50 = self.ta.sma(self.close, length=50)
        self.ma100 = self.ta.sma(self.close, length=100)
        self.daily_rsi = self.ta.rsi(self.close, length=self.d_rsi)
        self.weekly_rsi = resample_apply("W-FRI", resampled_rsi, self.close, self.w_rsi)

    def next(self):
        price = self.close[-1]
        if (
            not self.position
            and all(
                line.valid[-1]
                for line in (
                    self.daily_rsi,
                    self.weekly_rsi,
                    self.ma10,
                    self.ma20,
                    self.ma50,
                    self.ma100,
                )
            )
            and self.daily_rsi[-1] > self.level
            and (self.weekly_rsi[-1] > self.level)
            and (self.weekly_rsi[-1] > self.daily_rsi[-1])
            and (self.ma10[-1] > self.ma20[-1] > self.ma50[-1] > self.ma100[-1])
            and (price > self.ma10[-1])
        ):
            self.buy(
                percent=95,
                sl=0.92 * price,
            )
        elif self.ma10.valid[-1] and price < 0.98 * self.ma10[-1]:
            self.position.close()


def main():
    stats = Backtest(GOOG, System, commission=0.002).run()
    print(stats)
    return stats


if __name__ == "__main__":
    main()
