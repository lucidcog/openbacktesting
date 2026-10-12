"""原生参数优化与评分表：默认四组 grid，--method sambo 显式选择可选优化器。

随包 GOOG 日线；grid 无额外依赖，SAMBO 需要 optimize extra。普通类参数供原生优化使用，
不迁移到当前不支持 SAMBO 的 inputs。n1/n2 是趋势周期，n_enter/n_exit 是入场/退出周期。
手续费 0.2%、期末不强制平仓，最大化期末权益；固定种子不保证样本外有效。
输出最佳运行统计、评分表及按趋势周期聚合的均值；SAMBO 最多尝试 40 次，成本更高。
"""

import argparse

from openbacktesting import Backtest, Strategy
from openbacktesting.test import GOOG


class Sma4Cross(Strategy):
    n1 = 50
    n2 = 100
    n_enter = 20
    n_exit = 10

    def init(self):
        self.sma1 = self.ta.sma(self.close, length=self.n1)
        self.sma2 = self.ta.sma(self.close, length=self.n2)
        self.sma_enter = self.ta.sma(self.close, length=self.n_enter)
        self.sma_exit = self.ta.sma(self.close, length=self.n_exit)

    def next(self):
        if not self.position:
            if self.sma1[-1] > self.sma2[-1]:
                if self.ta.is_crossover(self.data.Close, self.sma_enter):
                    self.buy(percent=95)
            elif self.ta.is_crossover(self.sma_enter, self.data.Close):
                self.sell(percent=95)
        elif (
            self.position.is_long
            and self.ta.is_crossover(self.sma_exit, self.data.Close)
            or (self.position.is_short and self.ta.is_crossover(self.data.Close, self.sma_exit))
        ):
            self.position.close()


def ordered_periods(params):
    return params.n_exit < params.n_enter < params.n1 < params.n2


def main(method="grid"):
    if method not in ("grid", "sambo"):
        raise ValueError("method 必须为 grid 或 sambo")
    if method == "sambo":
        try:
            import sambo  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "SAMBO 需要额外依赖：pip install 'openbacktesting[optimize]'"
            ) from exc
    bt = Backtest(GOOG, Sma4Cross, commission=0.002)
    common = {
        "constraint": ordered_periods,
        "maximize": "Equity Final [$]",
        "random_state": 0,
        "return_heatmap": True,
    }
    if method == "grid":
        # 2 × 2 × 1 × 1，四组均满足周期约束；不随机抽样。
        stats, heatmap = bt.optimize(
            n1=[40, 50],
            n2=[80, 100],
            n_enter=[20],
            n_exit=[10],
            **common,
        )
        optimization = None
    else:
        stats, heatmap, optimization = bt.optimize(
            n1=[10, 100],
            n2=[20, 200],
            n_enter=[10, 40],
            n_exit=[10, 30],
            method="sambo",
            max_tries=40,
            return_optimization=True,
            **common,
        )
    print(stats)
    print(heatmap.sort_values().tail(3))
    print(heatmap.groupby(["n1", "n2"]).mean().unstack())
    return stats, heatmap, optimization


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=("grid", "sambo"), default="grid")
    main(parser.parse_args().method)
