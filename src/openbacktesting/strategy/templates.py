"""从 lib 迁入的既有实现：SignalStrategy, TrailingStrategy。"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from openbacktesting.helpers import _set_legacy_module
from openbacktesting.strategy.base import Strategy


class SignalStrategy(Strategy):
    """按预计算的进入与退出信号运行的可组合策略基类。


    A simple helper strategy that operates on position entry/exit signals.
    This makes the backtest of the strategy simulate a [vectorized backtest].
    用法见使用手册的可运行示例。

    [vectorized backtest]: https://altpower.app/?q=vectorized+backtest

    To use this helper strategy, subclass it, override its
    `openbacktesting.engine.Strategy.init` method,
    and set the signal vector by calling
    `openbacktesting.lib.SignalStrategy.set_signal` method from within it.

        class ExampleStrategy(SignalStrategy):
            def init(self):
                super().init()
                self.set_signal(sma1 > sma2, sma1 < sma2)

    Remember to call `super().init()` and `super().next()` in your
    overridden methods.
    """

    __entry_signal = (0,)
    __exit_signal = (False,)

    def set_signal(
        self,
        entry_size: Sequence[float],
        exit_portion: Sequence[float] | None = None,
    ):
        """登记真实资产数量及退出比例序列；正数开多、负数开空，零不入场。


        Set entry/exit signal vectors (arrays).

        A long entry signal is considered present wherever `entry_size`
        is greater than zero, and a short signal wherever `entry_size`
        is less than zero, following `openbacktesting.engine.Order.size` semantics.

        If `exit_portion` is provided, a nonzero value closes portion the position
        (see `openbacktesting.engine.Trade.close()`) in the respective direction
        (positive values close long trades, negative short).

        稀疏信号不影响逐根回调，NaN 不触发交易。
        """
        self.__entry_signal = self.ind(  # type: ignore
            lambda: pd.Series(entry_size, dtype=float).replace(0, np.nan).to_numpy(),
            name="entry size",
        )

        if exit_portion is not None:
            self.__exit_signal = self.ind(  # type: ignore
                lambda: pd.Series(exit_portion, dtype=float).replace(0, np.nan).to_numpy(),
                name="exit portion",
            )

    def next(self):
        super().next()

        exit_portion = self.__exit_signal[-1]
        if exit_portion > 0:
            for trade in self.trades:
                if trade.is_long:
                    trade.close(exit_portion)
        elif exit_portion < 0:
            for trade in self.trades:
                if trade.is_short:
                    trade.close(-exit_portion)

        entry_size = self.__entry_signal[-1]
        if entry_size > 0:
            self.buy(qty=entry_size)
        elif entry_size < 0:
            self.sell(qty=-entry_size)


class TrailingStrategy(Strategy):
    """依据 ATR 更新交易止损的可组合策略基类。


    A strategy with automatic trailing stop-loss, trailing the current
    price at distance of some multiple of average true range (ATR). Call
    `TrailingStrategy.set_trailing_sl()` to set said multiple
    (`6` by default).
    用法见使用手册的可运行示例。


    Remember to call `super().init()` and `super().next()` in your
    overridden methods.
    """

    __n_atr = 6.0
    __atr = None
    __pct = None

    def init(self):
        super().init()
        self.set_atr_periods()

    def set_atr_periods(self, periods: int = 100):
        """设置因果 ATR 窗口；默认100，预热期不回填、不设置 ATR 止损。"""
        hi, lo, c_prev = self.data.High, self.data.Low, pd.Series(self.data.Close).shift(1)
        tr = np.max([hi - lo, (c_prev - hi).abs(), (c_prev - lo).abs()], axis=0)
        atr = pd.Series(tr).rolling(periods).mean().values
        self.__atr = atr

    def set_trailing_sl(self, n_atr: float = 6):
        """设置后续跟踪止损使用的 ATR 倍数。


        Set the future trailing stop-loss as some multiple (`n_atr`)
        average true bar ranges away from the current price.
        """
        self.__n_atr = n_atr
        self.__pct = None

    def set_trailing_pct(self, pct: float = 0.05):
        """按当前已确认价格计算百分比距离，默认5%，不使用全样本估计。

        pct必须在0与1之间。多头止损仅上移、空头仅下移；更新最早下一根生效。
        next逐根调用；ATR未就绪时跳过止损更新，百分比模式不依赖ATR。
        """
        assert 0 < pct < 1, "Need pct= as rate, i.e. 5% == 0.05"
        self.__pct = pct

    def next(self):
        super().next()
        # Can't use index=-1 because self.__atr is not an Indicator type
        index = len(self.data) - 1
        distance = (
            self.data.Close[index] * self.__pct
            if self.__pct is not None
            else self.__atr[index] * self.__n_atr
        )
        if not np.isfinite(distance):
            return
        for trade in self.trades:
            if trade.is_long:
                trade.sl = max(trade.sl or -np.inf, self.data.Close[index] - distance)
            else:
                trade.sl = min(trade.sl or np.inf, self.data.Close[index] + distance)


_set_legacy_module(SignalStrategy, "openbacktesting.lib")
_set_legacy_module(TrailingStrategy, "openbacktesting.lib")
