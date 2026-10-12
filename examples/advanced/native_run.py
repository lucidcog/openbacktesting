"""原生回测与结果消费：显式调用 main，区别于只导出 bt 的作者模板。

随包 GOOG 日线，无额外依赖。普通类参数 n1/n2 控制内置 SMA 周期；
本例保留原生 API 与双向交叉策略，初始资金 10000、手续费 0.2%，期末不强制平仓。
输出统计、权益曲线与交易表；参数优化参见同目录 parameter_optimization.py。
"""

from openbacktesting import Backtest, Strategy
from openbacktesting.test import GOOG


class SmaCross(Strategy):
    n1 = 10
    n2 = 20

    def init(self):
        self.sma1 = self.ta.sma(self.close, length=self.n1)
        self.sma2 = self.ta.sma(self.close, length=self.n2)

    def next(self):
        if self.ta.is_crossover(self.sma1, self.sma2):
            self.position.close()
            self.buy(percent=95)
        elif self.ta.is_crossunder(self.sma1, self.sma2):
            self.position.close()
            self.sell(percent=95)


def main():
    bt = Backtest(GOOG, SmaCross, cash=10000, commission=0.002)
    stats = bt.run()
    print(stats)
    print(stats["_equity_curve"].tail())
    print(stats["_trades"].tail())
    return stats


if __name__ == "__main__":
    main()
