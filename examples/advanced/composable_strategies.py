"""组合 SignalStrategy 与 TrailingStrategy：向量入场信号叠加移动止损。

随包 GOOG 日线、无额外依赖；n1/n2 是快慢 SMA 周期。覆盖 init/next 时须调用 super。
只做多、每笔使用请求时权益的 95%、移动止损为 2 倍 ATR、手续费 0.2%。
期末不强制平仓；显式执行 main 后输出统计，不代表止损可以保证盈利。
"""

import pandas as pd
from openbacktesting import Backtest
from openbacktesting.lib import SignalStrategy, TrailingStrategy
from openbacktesting.test import GOOG


class SmaCross(SignalStrategy, TrailingStrategy):
    n1 = 10
    n2 = 25

    def init(self):
        super().init()
        sma1 = self.ta.sma(self.close, length=self.n1)
        sma2 = self.ta.sma(self.close, length=self.n2)
        signal = (pd.Series(sma1) > sma2).astype(int).diff().fillna(0)
        signal = signal.replace(-1, 0)
        self.entry_signal = signal.to_numpy()
        self.set_trailing_sl(2)

    def next(self):
        super().next()
        if self.entry_signal[len(self.data) - 1] > 0:
            self.buy(percent=95)


def main():
    stats = Backtest(GOOG, SmaCross, commission=0.002).run()
    print(stats)
    return stats


if __name__ == "__main__":
    main()
