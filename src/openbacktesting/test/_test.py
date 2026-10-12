import inspect
import multiprocessing as mp
import os
import subprocess
import sys
import time
import unittest
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import contextmanager
from functools import partial
from glob import glob
from pathlib import Path
from tempfile import gettempdir
from unittest import TestCase

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from openbacktesting import Backtest as _Backtest
from openbacktesting import Strategy
from openbacktesting._util import _Array, _as_str, _Indicator, patch, try_
from openbacktesting.lib import (
    OHLCV_AGG,
    FractionalBacktest,
    MultiBacktest,
    SignalStrategy,
    TrailingStrategy,
    barssince,
    compute_stats,
    quantile,
    random_ohlc_data,
    resample_apply,
)
from openbacktesting.portfolio.stats import compute_drawdown_duration_peaks
from openbacktesting.strategy.sizing import equity_fraction
from openbacktesting.test import BTCUSD, EURUSD, GOOG, SMA

SHORT_DATA = GOOG.iloc[:20]  # Short data for fast tests with no indicator lag

# Avoid the 'Some trades remain open' warning in many tests
Backtest = partial(_Backtest, end_policy="close_at_last_close")


@contextmanager
def chdir(path):
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


class SmaCross(Strategy):
    # NOTE: These values are also used on the website!
    fast = 10
    slow = 30

    def init(self):
        self.sma1 = self.ind(SMA, self.data.Close, self.fast)
        self.sma2 = self.ind(SMA, self.data.Close, self.slow)

    def next(self):
        if self.ta.is_crossover(self.sma1, self.sma2):
            self.position.close()
            self.buy(
                qty=equity_fraction(
                    0.95,
                    account=self.account,
                    reference_price=self.close[-1],
                    instrument=self.instrument,
                ).qty
            )
        elif self.ta.is_crossunder(self.sma1, self.sma2):
            self.position.close()
            self.sell(
                qty=equity_fraction(
                    0.95,
                    account=self.account,
                    reference_price=self.close[-1],
                    instrument=self.instrument,
                ).qty
            )


class _S(Strategy):
    def init(self):
        super().init()


class TestBacktest(TestCase):
    def test_run(self):
        bt = Backtest(EURUSD, SmaCross)
        bt.run()

    def test_run_invalid_param(self):
        bt = Backtest(GOOG, SmaCross)
        self.assertRaises(AttributeError, bt.run, foo=3)

    def test_run_speed(self):
        # CPU 性能阈值在无插桩解释器测量；功能与分支仍由完整回归采集覆盖率。
        process = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                """
import sys
import time
from openbacktesting.test._test import Backtest, GOOG, SmaCross
assert "coverage" not in sys.modules
bt = Backtest(GOOG, SmaCross)
start = time.process_time()
bt.run()
print(time.process_time() - start)
""",
            ],
            env={
                key: value for key, value in os.environ.items() if not key.startswith("COVERAGE_")
            },
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        self.assertLess(float(process.stdout), 0.3)

    def test_data_missing_columns(self):
        df = GOOG.copy(deep=False)
        del df["Open"]
        with self.assertRaises(ValueError):
            Backtest(df, SmaCross).run()

    def test_data_nan_columns(self):
        df = GOOG.copy()
        df["Open"] = np.nan
        with self.assertRaises(ValueError):
            Backtest(df, SmaCross).run()

    def test_data_extra_columns(self):
        df = GOOG.copy(deep=False)
        df["P/E"] = np.arange(len(df))
        df["MCap"] = np.arange(len(df))

        class S(Strategy):
            def init(self):
                assert len(self.data.MCap) == len(self.data.Close)
                assert len(self.data["P/E"]) == len(self.data.Close)

            def next(self):
                assert len(self.data.MCap) == len(self.data.Close)
                assert len(self.data["P/E"]) == len(self.data.Close)

        Backtest(df, S).run()

    def test_data_invalid(self):
        with self.assertRaises(TypeError):
            Backtest(GOOG.index, SmaCross).run()
        with self.assertRaises(ValueError):
            Backtest(GOOG.iloc[:0], SmaCross).run()

    def test_assertions(self):
        class Assertive(Strategy):
            def init(self):
                self.sma = self.ind(SMA, self.data.Close, 10)
                self.remains_indicator = self.ind(
                    lambda: np.r_[2] * np.cumsum(self.sma * 5 + 1) * np.r_[2]
                )

                self.transpose_invalid = self.ind(
                    lambda: np.column_stack((self.data.Open, self.data.Close))
                )

                resampled = resample_apply("W", SMA, self.data.Close, 3)
                resampled_ind = resample_apply("W", SMA, self.sma, 3)
                assert np.unique(resampled[-5:]).size == 1
                assert np.unique(resampled[-6:]).size == 2
                assert any(item is resampled for item in self._indicators), (
                    "Strategy.ind not called"
                )
                assert any(item is resampled_ind for item in self._indicators), (
                    "Strategy.ind not called"
                )

                assert 1 == try_(lambda: self.data.X, 1, AttributeError)
                assert 1 == try_(lambda: self.data["X"], 1, KeyError)

                assert self.data.pip == 0.01

                assert float(self.data.Close) == self.data.Close[-1]

            def next(self, _FEW_DAYS=pd.Timedelta("3 days")):  # noqa: B008 — 初始化时固定默认值，保持原生行为
                assert self.equity >= 0

                from openbacktesting.indicator_types import IndicatorHandle

                assert isinstance(self.sma, IndicatorHandle)
                assert isinstance(self.remains_indicator, IndicatorHandle)
                assert self.remains_indicator.name
                assert isinstance(self.remains_indicator._opts, dict)

                assert not np.isnan(self.data.Open[-1])
                assert not np.isnan(self.data.High[-1])
                assert not np.isnan(self.data.Low[-1])
                assert not np.isnan(self.data.Close[-1])
                assert not np.isnan(self.data.Volume[-1])
                assert bool(self.sma.valid[-1]) == bool(np.isfinite(self.sma[-1]))
                assert self.data.index[-1]

                _ = self.position
                _ = self.position.size
                _ = self.position.pl
                _ = self.position.return_fraction
                _ = self.position.is_long

                if self.ta.is_crossover(self.sma, self.data.Close):
                    for order in self.orders:
                        if not order.is_contingent:
                            order.cancel()
                    price = self.data.Close[-1]
                    sl, tp = 1.05 * price, 0.9 * price

                    n_orders = len(self.orders)
                    self.sell(
                        qty=equity_fraction(
                            0.21,
                            account=self.account,
                            reference_price=self.close[-1],
                            instrument=self.instrument,
                        ).qty,
                        limit=price,
                        stop=price,
                        sl=sl,
                        tp=tp,
                    )
                    assert len(self.orders) == n_orders + 1

                    order = self.orders[-1]
                    assert order.limit == price
                    assert order.stop == price
                    assert (
                        order.size
                        == -equity_fraction(0.21, account=self.account, reference_price=price).qty
                    )
                    assert order.sl == sl
                    assert order.tp == tp
                    assert not order.is_contingent

                elif self.position:
                    assert not self.position.is_long
                    assert self.position.is_short
                    assert self.position.pl
                    assert self.position.return_fraction
                    assert self.position.size < 0

                    trade = self.trades[0]
                    if self.data.index[-1] - self.data.index[trade.entry_bar] > _FEW_DAYS:
                        assert not trade.is_long
                        assert trade.is_short
                        assert trade.size < 0
                        assert trade.entry_bar > 0
                        assert isinstance(trade.entry_time, pd.Timestamp)
                        assert trade.exit_bar is None
                        assert trade.exit_time is None
                        assert trade.entry_price > 0
                        assert trade.exit_price is None
                        assert trade.pl / 1
                        assert trade.return_fraction / 1
                        assert trade.value > 0
                        assert trade.sl
                        assert trade.tp
                        # Close multiple times
                        self.position.close(0.5 if abs(self.position.size) >= 2 else 1)
                        self.position.close(0.5 if abs(self.position.size) >= 2 else 1)
                        self.position.close(0.5 if abs(self.position.size) >= 2 else 1)
                        self.position.close()
                        self.position.close()

        bt = Backtest(GOOG, Assertive)
        stats = bt.run()
        self.assertEqual(stats["# Trades"], 267)  # 显式数量与向零分批退出的政策v2基线

    def test_broker_params(self):
        bt = Backtest(
            GOOG.iloc[:100],
            SmaCross,
            cash=1000,
            spread=0.01,
            margin=0.1,
            execution_timing="same_close",
        )
        bt.run()

    def test_absolute_size_order_warns_on_insufficient_margin(self):
        class S(Strategy):
            def init(self):
                pass

            def next(self):
                self.buy(qty=10_000)

        bt = Backtest(GOOG.iloc[:3], S, cash=1000)
        stats = bt.run()
        self.assertIn("insufficient_funds", stats._orders.reason.dropna().tolist())
        self.assertEqual(stats["# Trades"], 0)

    def test_spread_commission(self):
        class S(Strategy):
            def init(self):
                self.done = False

            def next(self):
                if not self.position:
                    self.buy(
                        qty=equity_fraction(
                            0.95,
                            account=self.account,
                            reference_price=self.close[-1],
                            instrument=self.instrument,
                        ).qty
                    )
                else:
                    self.position.close()
                    self.next = lambda: None  # Done

        qty = int(10_000 * 0.95 / SHORT_DATA.Close.iloc[0])
        for spread, commission in ((0.01, 0.01), (0, (100, 0.01)), (0, lambda q, p: q * p * 0.01)):
            stats = Backtest(SHORT_DATA, S, spread=spread, commission=commission).run()
            entry = min(SHORT_DATA.High.iloc[1], SHORT_DATA.Open.iloc[1] * (1 + spread))
            exit_price = max(SHORT_DATA.Low.iloc[2], SHORT_DATA.Open.iloc[2] * (1 - spread))

            def fee(q, price, commission=commission):
                if callable(commission):
                    return commission(q, price)
                fixed, relative = commission if isinstance(commission, tuple) else (0, commission)
                return fixed + abs(q) * price * relative

            expected = [
                10_000 - fee(qty, entry) + qty * (SHORT_DATA.Close.iloc[1] - entry),
                10_000 - fee(qty, entry) - fee(-qty, exit_price) + qty * (exit_price - entry),
            ]
            np.testing.assert_allclose(stats._equity_curve.Equity.iloc[1:3], expected)
            self.assertEqual(stats._trades.EntryPrice.iloc[0], entry)
            self.assertEqual(stats._trades.ExitPrice.iloc[0], exit_price)

    def test_commissions(self):
        class S(_S):
            def next(self):
                if len(self.data) == 2:
                    self.buy(qty=SIZE, tp=3)

        FIXED_COMMISSION, COMMISSION = 10, 0.01
        CASH, SIZE, PRICE_ENTRY, PRICE_EXIT = 5000, 100, 1, 4
        arr = np.r_[1, PRICE_ENTRY, 1, 2, PRICE_EXIT, 1, 2]
        df = pd.DataFrame({"Open": arr, "High": arr, "Low": arr, "Close": arr})
        with self.assertWarnsRegex(UserWarning, "index is not datetime"):
            stats = Backtest(df, S, cash=CASH, commission=(FIXED_COMMISSION, COMMISSION)).run()
        EXPECTED_PAID_COMMISSION = (
            FIXED_COMMISSION
            + COMMISSION * SIZE * PRICE_ENTRY
            + FIXED_COMMISSION
            + COMMISSION * SIZE * PRICE_EXIT
        )
        self.assertEqual(stats["Commissions [$]"], EXPECTED_PAID_COMMISSION)
        self.assertEqual(stats._trades["Commission"][0], EXPECTED_PAID_COMMISSION)
        self.assertEqual(
            stats["Equity Final [$]"],
            CASH + (PRICE_EXIT - PRICE_ENTRY) * SIZE - EXPECTED_PAID_COMMISSION,
        )

    def test_dont_overwrite_data(self):
        df = EURUSD.copy()
        bt = Backtest(df, SmaCross)
        bt.run()
        bt.optimize(fast=4, slow=[6, 8])
        self.assertTrue(df.equals(EURUSD))

    def test_strategy_abstract(self):
        class MyStrategy(Strategy):
            pass

        self.assertRaises(TypeError, MyStrategy, None, None)

    def test_strategy_str(self):
        bt = Backtest(GOOG.iloc[:100], SmaCross)
        self.assertEqual(str(bt.run()._strategy), SmaCross.__name__)
        self.assertEqual(str(bt.run(fast=11)._strategy), SmaCross.__name__ + "(fast=11)")

    def test_compute_drawdown(self):
        dd = pd.Series([0, 1, 7, 0, 4, 0, 0])
        durations, peaks = compute_drawdown_duration_peaks(dd)
        np.testing.assert_array_equal(durations, pd.Series([3, 2], index=[3, 5]).reindex(dd.index))
        np.testing.assert_array_equal(peaks, pd.Series([7, 4], index=[3, 5]).reindex(dd.index))

    def test_compute_stats(self):
        stats = Backtest(GOOG, SmaCross, end_policy="close_at_last_close").run()
        # 政策v2：显式95%数量预算、末Close清算；原历史基线文件保留。
        # 逐根执行：买入持有从输入首根计算；风险年化包含首个零收益日桶。
        # 交易、权益、Beta 和回撤均未变化，Alpha 随市场对照调整。
        expected = pd.Series(
            {
                "Start": pd.Timestamp("2004-08-19 00:00:00"),
                "End": pd.Timestamp("2013-03-01 00:00:00"),
                "Duration": pd.Timedelta("3116 days 00:00:00"),
                "Exposure Time [%]": 96.74115456238361,
                "Equity Final [$]": 49228.00999999996,
                "Equity Peak [$]": 70110.02999999998,
                "Return [%]": 392.28009999999955,
                "Buy & Hold Return [%]": 703.4582419772772,
                "Return (Ann.) [%]": 20.561671886086728,
                "Volatility (Ann.) [%]": 34.57340358414538,
                "CAGR [%]": 20.542294223341152,
                "Sharpe Ratio": 0.5947251284081232,
                "Sortino Ratio": 1.104726320298045,
                "Calmar Ratio": 0.4462810975723509,
                "Alpha [%]": 365.639613282582,
                "Beta": 0.03787074360311223,
                "Max. Drawdown [%]": -46.07336496646776,
                "Avg. Drawdown [%]": -5.747302647122755,
                "Max. Drawdown Duration": pd.Timedelta("584 days 00:00:00"),
                "Avg. Drawdown Duration": pd.Timedelta("40 days 00:00:00"),
                "# Trades": 66,
                "Win Rate [%]": 46.96969696969697,
                "Best Trade [%]": 53.59595229490424,
                "Worst Trade [%]": -18.398873538354813,
                "Avg. Trade [%]": 2.5479693282886906,
                "Max. Trade Duration": pd.Timedelta("183 days 00:00:00"),
                "Avg. Trade Duration": pd.Timedelta("46 days 00:00:00"),
                "Profit Factor": 2.174469316409448,
                "Expectancy [%]": 3.293098628562828,
                "SQN": 1.1335447628114286,
                "Kelly Criterion": 0.158222363299374,
                "Commissions [$]": 0.0,
                "# Closed Lots": 66,
            }
        )

        def almost_equal(a, b):
            try:
                return np.isclose(a, b, rtol=1.0e-8)
            except TypeError:
                return a == b

        diff = {
            key: print(key) or value
            for key, value in stats.filter(regex="^[^_]").items()
            if not almost_equal(value, expected[key])
        }
        self.assertDictEqual(diff, {})

        self.assertSequenceEqual(
            sorted(stats["_equity_curve"].columns),
            sorted(["Equity", "DrawdownPct", "DrawdownDuration"]),
        )

        self.assertEqual(len(stats["_trades"]), 66)

        indicator_columns = [
            f"{entry}_SMA(C,{n})"
            for entry in ("Entry", "Exit")
            for n in (SmaCross.fast, SmaCross.slow)
        ]
        self.assertSequenceEqual(
            sorted(stats["_trades"].columns),
            sorted(
                [
                    "Size",
                    "EntryBar",
                    "ExitBar",
                    "EntryPrice",
                    "ExitPrice",
                    "SL",
                    "TP",
                    "PnL",
                    "ReturnPct",
                    "EntryTime",
                    "ExitTime",
                    "Duration",
                    "Tag",
                    "Commission",
                    "trade_id",
                    "entry_fill_id",
                    "allocation_id",
                    "exit_fill_id",
                    "exit_sequence",
                    *indicator_columns,
                ]
            ),
        )

    def test_compute_stats_bordercase(self):

        class SingleTrade(Strategy):
            def init(self):
                self._done = False

            def next(self):
                if not self._done:
                    self.buy(
                        qty=equity_fraction(
                            0.95,
                            account=self.account,
                            reference_price=self.close[-1],
                            instrument=self.instrument,
                        ).qty
                    )
                    self._done = True
                if self.position:
                    self.position.close()

        class SinglePosition(_S):
            def next(self):
                if not self.position:
                    self.buy(
                        qty=equity_fraction(
                            0.95,
                            account=self.account,
                            reference_price=self.close[-1],
                            instrument=self.instrument,
                        ).qty
                    )

        class NoTrade(_S):
            def next(self):
                pass

        for strategy in (SmaCross, SingleTrade, SinglePosition, NoTrade):
            with self.subTest(strategy=strategy.__name__):
                stats = Backtest(GOOG.iloc[:100], strategy).run()

                self.assertFalse(np.isnan(stats["Equity Final [$]"]))
                self.assertFalse(stats["_equity_curve"]["Equity"].isnull().any())
                self.assertEqual(stats["_strategy"].__class__, strategy)

    def test_trade_enter_hit_sl_on_same_day(self):
        the_day = pd.Timestamp("2012-10-17 00:00:00")

        class S(_S):
            def next(self):
                if self.data.index[-1] == the_day:
                    self.buy(sl=720, qty=1)

        self.assertEqual(Backtest(GOOG, S).run()._trades.iloc[0].ExitPrice, 720)

        class S(_S):
            def next(self):
                if self.data.index[-1] == the_day:
                    self.buy(stop=758, sl=720, qty=1)

        result = Backtest(GOOG, S).run()
        self.assertEqual(result._trades.iloc[0].ExitPrice, 705.58)
        self.assertEqual(result.attrs["diagnostics"][0]["code"], "protection_next_bar")

    def test_stop_price_between_sl_tp(self):
        class S(_S):
            def next(self):
                if self.data.index[-1] == pd.Timestamp("2004-09-09 00:00:00"):
                    self.buy(stop=104, sl=103, tp=110, qty=1)

        self.assertEqual(Backtest(GOOG, S).run()._trades.iloc[0].EntryPrice, 104)

    def test_position_close_portion(self):
        class SmaCross(Strategy):
            def init(self):
                self.sma1 = self.ind(SMA, self.data.Close, 10)
                self.sma2 = self.ind(SMA, self.data.Close, 20)

            def next(self):
                if not self.position and self.ta.is_crossover(self.sma1, self.sma2):
                    self.buy(qty=10)
                if self.position and self.ta.is_crossunder(self.sma1, self.sma2):
                    self.position.close(portion=0.5 if abs(self.position.size) >= 2 else 1)

        bt = Backtest(GOOG, SmaCross, spread=0.002)
        bt.run()

    def test_close_orders_from_last_strategy_iteration(self):
        class S(_S):
            def next(self):
                if not self.position:
                    self.buy(
                        qty=equity_fraction(
                            0.95,
                            account=self.account,
                            reference_price=self.close[-1],
                            instrument=self.instrument,
                        ).qty
                    )
                elif len(self.data) == len(SHORT_DATA):
                    self.position.close()

        result = Backtest(SHORT_DATA, S, end_policy="mark_to_market").run()
        self.assertTrue(result._trades.empty)
        self.assertEqual(result._orders.iloc[-1].reason, "end_of_data")
        self.assertFalse(
            Backtest(SHORT_DATA, S, end_policy="close_at_last_close").run()._trades.empty
        )

    def test_check_adjusted_price_when_placing_order(self):
        class S(_S):
            def next(self):
                self.buy(tp=self.data.Close * 1.01, qty=1)

        self.assertRaises(TypeError, Backtest(SHORT_DATA, S, spread=0.02).run)


class TestStrategy(TestCase):
    @staticmethod
    def _Backtest(strategy_coroutine, data=SHORT_DATA, **kwargs):
        class S(Strategy):
            def init(self):
                self.step = strategy_coroutine(self)

            def next(self):
                try_(self.step.__next__, None, StopIteration)

        return Backtest(data, S, **kwargs)

    def test_position(self):
        def coroutine(self):
            yield self.buy(
                qty=equity_fraction(
                    0.95,
                    account=self.account,
                    reference_price=self.close[-1],
                    instrument=self.instrument,
                ).qty
            )

            assert self.position
            assert self.position.is_long
            assert not self.position.is_short
            assert self.position.size > 0
            assert self.position.pl
            assert self.position.return_fraction

            yield self.position.close()

            assert not self.position
            assert not self.position.is_long
            assert not self.position.is_short
            assert not self.position.size
            assert not self.position.pl
            assert not self.position.return_fraction

        self._Backtest(coroutine).run()

    def test_broker_hedging(self):
        def coroutine(self):
            yield self.buy(qty=2)

            assert len(self.trades) == 1
            yield self.sell(qty=1)

            assert len(self.trades) == 2

        self._Backtest(coroutine, hedging=True).run()

    def test_broker_exclusive_orders(self):
        def coroutine(self):
            yield self.buy(qty=2)

            assert len(self.trades) == 1
            yield self.sell(qty=3)

            assert len(self.trades) == 1
            assert self.trades[0].size == -3

        self._Backtest(coroutine, exclusive_orders=True).run()

    def test_trade_multiple_close(self):
        def coroutine(self):
            yield self.buy(
                qty=equity_fraction(
                    0.95,
                    account=self.account,
                    reference_price=self.close[-1],
                    instrument=self.instrument,
                ).qty
            )

            assert self.trades
            self.trades[-1].close(1)
            self.trades[-1].close(0.1)
            yield

        self._Backtest(coroutine).run()

    def test_close_trade_leaves_needsize_0(self):
        def coroutine(self):
            self.buy(qty=1)
            self.buy(qty=1)
            yield
            if self.position:
                self.sell(qty=1)

        self._Backtest(coroutine).run()

    def test_stop_limit_order_price_is_stop_price(self):
        def coroutine(self):
            yield  # 此价格回归固定在第二根提交，独立于新增首根回调。
            self.buy(stop=112, limit=113, qty=1)
            self.sell(stop=107, limit=105, qty=1)
            yield

        stats = self._Backtest(coroutine).run()
        self.assertListEqual(stats._trades.filter(like="Price").stack().tolist(), [112, 107])

    def test_autoclose_trades_on_finish(self):
        def coroutine(self):
            yield self.buy(
                qty=equity_fraction(
                    0.95,
                    account=self.account,
                    reference_price=self.close[-1],
                    instrument=self.instrument,
                ).qty
            )

        stats = self._Backtest(coroutine, end_policy="close_at_last_close").run()
        self.assertEqual(len(stats._trades), 1)

    def test_order_tag(self):
        def coroutine(self):
            yield self.buy(qty=2, tag=1)
            yield self.sell(qty=1, tag="s")
            yield self.sell(qty=1)

            yield self.buy(tag=2, qty=1)
            yield self.position.close()

        stats = self._Backtest(coroutine).run()
        self.assertEqual(list(stats._trades.Tag), [1, 1, 2])


class TestOptimize(TestCase):
    def test_optimize(self):
        bt = Backtest(GOOG.iloc[:100], SmaCross)
        OPT_PARAMS = {"fast": range(2, 5, 2), "slow": [2, 5, 7, 9]}

        self.assertRaises(ValueError, bt.optimize)
        self.assertRaises(ValueError, bt.optimize, maximize="missing key", **OPT_PARAMS)
        self.assertRaises(ValueError, bt.optimize, maximize="missing key", **OPT_PARAMS)
        self.assertRaises(TypeError, bt.optimize, maximize=15, **OPT_PARAMS)
        self.assertRaises(TypeError, bt.optimize, constraint=15, **OPT_PARAMS)
        self.assertRaises(ValueError, bt.optimize, constraint=lambda d: False, **OPT_PARAMS)
        self.assertRaises(ValueError, bt.optimize, return_optimization=True, **OPT_PARAMS)

        res = bt.optimize(**OPT_PARAMS)
        self.assertIsInstance(res, pd.Series)

        default_maximize = inspect.signature(bt.optimize).parameters["maximize"].default
        res2 = bt.optimize(**OPT_PARAMS, maximize=lambda s: s[default_maximize])
        self.assertDictEqual(
            res.filter(regex="^[^_]").fillna(-1).to_dict(),
            res2.filter(regex="^[^_]").fillna(-1).to_dict(),
        )

        _res3, heatmap = bt.optimize(
            **OPT_PARAMS, return_heatmap=True, constraint=lambda d: d.slow > 2 * d.fast
        )
        self.assertIsInstance(heatmap, pd.Series)
        self.assertEqual(len(heatmap), 4)
        self.assertEqual(heatmap.name, default_maximize)

    def test_method_sambo(self):
        bt = Backtest(GOOG.iloc[:100], SmaCross, end_policy="close_at_last_close")
        res, heatmap, sambo_results = bt.optimize(
            fast=range(2, 20),
            slow=np.arange(2, 20, dtype=object),
            constraint=lambda p: p.fast < p.slow,
            max_tries=30,
            method="sambo",
            return_optimization=True,
            return_heatmap=True,
            random_state=2,
        )
        self.assertIsInstance(res, pd.Series)
        self.assertIsInstance(heatmap, pd.Series)
        self.assertGreater(heatmap.max(), 1.1)
        self.assertGreater(heatmap.min(), -2)
        self.assertEqual(-sambo_results.fun, heatmap.max())
        self.assertEqual(heatmap.index.tolist(), heatmap.dropna().index.unique().tolist())

    def test_max_tries(self):
        bt = Backtest(GOOG.iloc[:100], SmaCross)
        OPT_PARAMS = {"fast": range(2, 10, 2), "slow": [2, 5, 7, 9]}
        for method, max_tries, random_state in (
            ("grid", 5, 0),
            ("grid", 0.3, 0),
            ("sambo", 6, 0),
            ("sambo", 0.42, 0),
        ):
            with self.subTest(method=method, max_tries=max_tries, random_state=random_state):
                _, heatmap = bt.optimize(
                    max_tries=max_tries,
                    method=method,
                    random_state=random_state,
                    return_heatmap=True,
                    **OPT_PARAMS,
                )
                if method == "grid":
                    self.assertEqual(len(heatmap), 6)
                else:
                    # SAMBO可以因目标收敛提前结束；预算是上限。
                    self.assertTrue(0 < len(heatmap) <= 6)
                    self.assertTrue(heatmap.index.is_unique)

    def test_optimize_invalid_param(self):
        bt = Backtest(GOOG.iloc[:100], SmaCross)
        self.assertRaises(AttributeError, bt.optimize, foo=range(3))
        self.assertRaises(ValueError, bt.optimize, fast=[])

    def test_optimize_no_trades(self):
        bt = Backtest(GOOG, SmaCross)
        stats = bt.optimize(fast=[3], slow=[3])
        self.assertTrue(stats.isnull().any())

    def test_optimize_speed(self):
        bt = Backtest(GOOG.iloc[:100], SmaCross)
        start = time.process_time()
        bt.optimize(fast=range(2, 20, 2), slow=range(10, 40, 2))
        end = time.process_time()
        print(end - start)
        self.assertLess(end - start, 15.0)


class TestCalculationRegressions(TestCase):
    def test_wellknown(self):
        class S(_S):
            def next(self):
                date = self.data.index[-1]
                if date == pd.Timestamp("Thu 19 Oct 2006"):
                    self.buy(stop=484, limit=466, qty=100)
                elif date == pd.Timestamp("Thu 30 Oct 2007"):
                    self.position.close()
                elif date == pd.Timestamp("Tue 11 Nov 2008"):
                    self.sell(
                        stop=self.data.Low[-1],
                        limit=324.90,  # High from 14 Nov
                        qty=200,
                    )

        bt = Backtest(GOOG, S, margin=0.1)
        stats = bt.run()
        trades = stats["_trades"]

        self.assertAlmostEqual(stats["Equity Peak [$]"], 46961)
        self.assertEqual(stats["Equity Final [$]"], -951)
        self.assertEqual(len(trades), 2)
        assert trades[["EntryTime", "ExitTime"]].equals(
            pd.DataFrame(
                {
                    "EntryTime": pd.to_datetime(["2006-11-01", "2008-11-14"]),
                    "ExitTime": pd.to_datetime(["2007-10-31", "2009-09-21"]),
                }
            )
        )
        assert trades["PnL"].round().equals(pd.Series([23469.0, -34420.0]))

    def test_indicator_name(self):
        test_self = self

        class S(Strategy):
            def init(self):
                def _SMA():
                    return SMA(self.data.Close, 5), SMA(self.data.Close, 10)

                test_self.assertRaises(TypeError, self.ind, _SMA, name=42)
                test_self.assertRaises(ValueError, self.ind, _SMA, name=("SMA One",))
                test_self.assertRaises(
                    ValueError, self.ind, _SMA, name=("SMA One", "SMA Two", "SMA Three")
                )

                self.ind(SMA, self.data.Close, 5)
                self.ind(SMA, self.data.Close, 5, name="My SMA")
                self.ind(SMA, self.data.Close, 5, name=("My SMA",))
                self.ind(_SMA)
                self.ind(_SMA, name="My SMA")
                self.ind(_SMA, name=("SMA One", "SMA Two"))

            def next(self):
                pass

        bt = Backtest(GOOG, S)
        bt.run()


class TestLib(TestCase):
    def test_barssince(self):
        self.assertEqual(barssince(np.r_[1, 0, 0]), 2)
        self.assertEqual(barssince(np.r_[0, 0, 0]), np.inf)
        self.assertEqual(barssince(np.r_[0, 0, 0], 0), 0)

    def test_quantile(self):
        self.assertEqual(quantile(np.r_[1, 3, 2], 0.5), 2)
        self.assertEqual(quantile(np.r_[1, 3, 2]), 0.5)

    def test_resample_apply(self):
        res = resample_apply("D", SMA, EURUSD.Close, 10)
        self.assertEqual(res.name, "C[D]")
        self.assertEqual(res.count() / res.size, 0.9634)
        np.testing.assert_almost_equal(
            res.iloc[-48:].unique().tolist(), [1.242643, 1.242381, 1.242275], decimal=6
        )

        def resets_index(*args):
            return pd.Series(SMA(*args).values)

        res2 = resample_apply("D", resets_index, EURUSD.Close, 10)
        self.assertTrue((res.dropna() == res2.dropna()).all())
        self.assertTrue((res.index == res2.index).all())

        res3 = resample_apply("D", None, EURUSD)
        self.assertIn("Volume", res3)

        res3 = resample_apply("D", lambda df: (df.Close, df.Close), EURUSD)
        self.assertIsInstance(res3, pd.DataFrame)

    def test_random_ohlc_data(self):
        generator = random_ohlc_data(GOOG, frac=1)
        new_data = next(generator)
        self.assertEqual(list(new_data.index), list(GOOG.index))
        self.assertEqual(new_data.shape, GOOG.shape)
        self.assertEqual(list(new_data.columns), list(GOOG.columns))

    def test_compute_stats(self):
        stats = Backtest(GOOG, SmaCross).run()
        only_long_trades = stats._trades[stats._trades.Size > 0]
        long_stats = compute_stats(
            stats=stats, trades=only_long_trades, data=GOOG, risk_free_rate=0.02
        )
        self.assertNotEqual(list(stats._equity_curve.Equity), list(long_stats._equity_curve.Equity))
        self.assertNotEqual(stats["Sharpe Ratio"], long_stats["Sharpe Ratio"])
        self.assertEqual(long_stats["# Trades"], len(only_long_trades))
        self.assertEqual(stats._strategy, long_stats._strategy)
        assert_frame_equal(long_stats._trades, only_long_trades)

    def test_SignalStrategy(self):
        class S(SignalStrategy):
            def init(self):
                sma = self.data.Close.s.rolling(10).mean()
                self.set_signal(self.data.Close > sma, self.data.Close < sma)

        stats = Backtest(GOOG, S).run()
        self.assertIn("Rejected", stats._orders.status.tolist())
        self.assertIn(stats["# Trades"], (1179, 1182))  # varies on different archs?

    def test_TrailingStrategy(self):
        class S(TrailingStrategy):
            def init(self):
                super().init()
                self.set_atr_periods(40)
                self.set_trailing_pct(0.1)
                self.set_trailing_sl(3)
                self.sma = self.ind(lambda: self.data.Close.s.rolling(10).mean())

            def next(self):
                super().next()
                if not self.position and self.data.Close > self.sma:
                    self.buy(
                        qty=equity_fraction(
                            0.95,
                            account=self.account,
                            reference_price=self.close[-1],
                            instrument=self.instrument,
                        ).qty
                    )

        stats = Backtest(GOOG, S).run()
        self.assertEqual(stats["# Trades"], 57)

    def test_FractionalBacktest(self):
        from openbacktesting.broker import InstrumentSpec

        with self.assertRaisesRegex(TypeError, "InstrumentSpec"):
            FractionalBacktest(BTCUSD, SmaCross)
        ubtc_bt = Backtest(
            BTCUSD["2015":],
            SmaCross,
            instrument=InstrumentSpec(quantity_step=1 / 1e6),
            cash=100,
            end_policy="close_at_last_close",
        )
        stats = ubtc_bt.run(fast=2, slow=3)
        self.assertEqual(stats["# Trades"], 42)
        trades = stats["_trades"]
        self.assertEqual(len(trades), 42)
        trade = trades.iloc[0]
        self.assertAlmostEqual(trade["EntryPrice"], 236.69)
        # 指标保留内部计算单位；显式换算后仍等于原价格基线。
        self.assertAlmostEqual(stats["_strategy"]._indicators[0][trade["EntryBar"]], 234.14)

    def test_MultiBacktest(self):
        import openbacktesting

        assert callable(getattr(openbacktesting, "Pool", None)), openbacktesting.__dict__
        for start_method in mp.get_all_start_methods():
            with (
                self.subTest(start_method=start_method),
                patch(openbacktesting, "Pool", mp.get_context(start_method).Pool),
            ):
                start_time = time.monotonic()
                btm = MultiBacktest(
                    [GOOG, EURUSD, BTCUSD], SmaCross, cash=100_000, end_policy="close_at_last_close"
                )
                res = btm.run(fast=2)
                self.assertIsInstance(res, pd.DataFrame)
                self.assertEqual(res.columns.tolist(), [0, 1, 2])
                heatmap = btm.optimize(fast=[2, 4], slow=[10, 20])
                self.assertIsInstance(heatmap, pd.DataFrame)
                self.assertEqual(heatmap.columns.tolist(), [0, 1, 2])
                print(start_method, time.monotonic() - start_time)

    class SometimesNoTrade(Strategy):
        def init(self):
            self._will_trade = len(self.data) == 20

        def next(self):
            if not self._will_trade:
                return
            if self.position:
                self.position.close()
            elif not self.closed_trades:
                self.buy(
                    qty=equity_fraction(
                        0.95,
                        account=self.account,
                        reference_price=self.close[-1],
                        instrument=self.instrument,
                    ).qty
                )

    def test_MultiBacktest_handles_mixed_no_trade_results(self):
        btm = MultiBacktest(
            [GOOG.iloc[:20], GOOG.iloc[:21], GOOG.iloc[:22]], self.SometimesNoTrade, cash=100_000
        )
        res = btm.run()
        self.assertEqual(res.loc["# Trades"].tolist(), [1, 0, 0])
        self.assertNotIsInstance(res.iloc[0, 0], pd.Series)


class TestUtil(TestCase):
    def test_as_str(self):
        def func():
            pass

        class Class:
            def __call__(self):
                pass

        self.assertEqual(_as_str("4"), "4")
        self.assertEqual(_as_str(4), "4")
        self.assertEqual(_as_str(_Indicator([1, 2], name="x")), "x")
        self.assertEqual(_as_str(func), "func")
        self.assertEqual(_as_str(Class), "Class")
        self.assertEqual(_as_str(Class()), "Class")
        self.assertEqual(_as_str(pd.Series([1, 2], name="x")), "x")
        self.assertEqual(_as_str(pd.DataFrame()), "df")
        self.assertEqual(_as_str(lambda x: x), "λ")
        for s in ("Open", "High", "Low", "Close", "Volume"):
            self.assertEqual(_as_str(_Array([1], name=s)), s[0])

    def test_patch(self):
        class Object:
            pass

        o = Object()
        o.attr = False
        with patch(o, "attr", True):
            self.assertTrue(o.attr)
        self.assertFalse(o.attr)

    def test_pandas_accessors(self):
        class S(Strategy):
            def init(self):
                close, index = self.data.Close, self.data.index
                assert close.s.equals(pd.Series(close, index=index))
                assert self.data.df["Close"].equals(pd.Series(close, index=index))
                self.data.df["new_key"] = 2 * close

            def next(self):
                close, index = self.data.Close, self.data.index
                assert close.s.equals(pd.Series(close, index=index))
                assert self.data.df["Close"].equals(pd.Series(close, index=index))
                assert self.data.df["new_key"].equals(pd.Series(self.data.new_key, index=index))

        Backtest(GOOG.iloc[:20], S).run()

    def test_indicators_picklable(self):
        bt = Backtest(SHORT_DATA, SmaCross)
        with ProcessPoolExecutor() as executor:
            stats = executor.submit(_Backtest.run, bt).result()
        assert stats._strategy._indicators[0]._opts, "._opts and .name were not unpickled"


class TestDocs(TestCase):
    DOCS_DIR = str(Path(__file__).resolve().parents[3])

    @unittest.skipUnless(os.path.isdir(DOCS_DIR), "docs dir doesn't exist")
    @unittest.skipUnless(
        sys.platform.startswith("linux"), "test_examples requires mp.start_method=fork"
    )
    def test_examples(self):
        from importlib.util import module_from_spec, spec_from_file_location
        from runpy import run_path
        from unittest.mock import patch as mock_patch

        import openbacktesting

        examples = glob(os.path.join(self.DOCS_DIR, "examples", "**", "*.py"), recursive=True)
        self.assertGreaterEqual(len(examples), 4)
        with (
            chdir(gettempdir()),
            patch(openbacktesting, "Pool", mp.get_context("fork").Pool),
        ):
            for file in examples:
                with self.subTest(example=os.path.basename(file)):
                    # 保留模块身份直至运行结束，fork 的任务队列仍需 pickle 策略类。
                    name = "_engine_example_" + Path(file).stem
                    spec = spec_from_file_location(name, file)
                    module = module_from_spec(spec)
                    with mock_patch.dict(sys.modules, {name: module}):
                        spec.loader.exec_module(module)
                        if hasattr(module, "main"):
                            result = module.main()
                        else:
                            host = run_path(
                                str(Path(self.DOCS_DIR) / "examples/advanced/run_author.py")
                            )
                            result = openbacktesting.runtime.run(
                                vars(module), **host["chart_for"](file)
                            )
                        self.assertIsNotNone(result)

    def test_backtest_run_docstring_contains_stats_keys(self):
        stats = Backtest(SHORT_DATA, SmaCross).run()
        for key in stats.index:
            self.assertIn(key, _Backtest.run.__doc__)

    def test_readme_contains_stats_keys(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "README.md")) as f:
            readme = f.read()
        stats = Backtest(SHORT_DATA, SmaCross).run()
        for key in stats.index:
            self.assertIn(key, readme)


class TestRegressions(TestCase):
    def test_gh_521(self):
        class S(_S):
            def next(self):
                if self.data.Close[-1] == 100:
                    self.buy(qty=1, sl=90)

        arr = np.r_[100, 100, 100, 50, 50]
        df = pd.DataFrame({"Open": arr, "High": arr, "Low": arr, "Close": arr})
        with self.assertWarnsRegex(UserWarning, "index is not datetime"):
            bt = Backtest(df, S, cash=100, execution_timing="same_close")
        result = bt.run()
        self.assertEqual(result._trades["ExitPrice"][0], 50)
        self.assertIn("insufficient_funds", result._orders.reason.dropna().tolist())

    def test_stats_annualized(self):
        stats = Backtest(GOOG.resample("W").agg(OHLCV_AGG), SmaCross).run()
        self.assertFalse(np.isnan(stats["Return (Ann.) [%]"]))
        self.assertEqual(round(stats["Return (Ann.) [%]"]), -3)

    def test_cancel_orders(self):
        class S(_S):
            def next(self):
                self.buy(sl=1, tp=1e3, qty=1)
                if self.position:
                    self.position.close()
                    for order in self.orders:
                        order.cancel()

        Backtest(SHORT_DATA, S).run()

    def test_trade_on_close_closes_trades_on_close(self):
        def coro(strat):
            yield strat.buy(qty=1, sl=90) and strat.buy(qty=1, sl=80)
            assert len(strat.trades) == 2
            yield strat.trades[0].close()
            yield

        arr = np.r_[100, 101, 102, 50, 51]
        df = pd.DataFrame({"Open": arr - 10, "Close": arr, "High": arr, "Low": arr - 10})
        with self.assertWarnsRegex(UserWarning, "index is not datetime"):
            trades = (
                TestStrategy._Backtest(coro, df, cash=250, execution_timing="same_close")
                .run()
                ._trades
            )
            # trades = Backtest(df, S, cash=250, trade_on_close=True).run()._trades
            self.assertEqual(trades["EntryBar"][0], 0)
            self.assertEqual(trades["ExitBar"][0], 1)
            self.assertEqual(trades["EntryPrice"][0], 100)
            self.assertEqual(trades["ExitPrice"][0], 101)
            self.assertEqual(trades["EntryBar"][1], 0)
            self.assertEqual(trades["ExitBar"][1], 3)
            self.assertEqual(trades["EntryPrice"][1], 100)
            self.assertEqual(trades["ExitPrice"][1], 40)

        with self.assertWarnsRegex(UserWarning, "index is not datetime"):
            trades = (
                TestStrategy._Backtest(coro, df, cash=250, execution_timing="next_open")
                .run()
                ._trades
            )
            # trades = Backtest(df, S, cash=250, trade_on_close=False).run()._trades
            self.assertEqual(trades["EntryBar"][0], 1)
            self.assertEqual(trades["ExitBar"][0], 2)
            self.assertEqual(trades["EntryPrice"][0], 91)
            self.assertEqual(trades["ExitPrice"][0], 92)
            self.assertEqual(trades["EntryBar"][1], 1)
            self.assertEqual(trades["ExitBar"][1], 3)
            self.assertEqual(trades["EntryPrice"][1], 91)
            self.assertEqual(trades["ExitPrice"][1], 40)

    def test_trades_dates_match_prices(self):
        bt = Backtest(EURUSD, SmaCross, execution_timing="same_close")
        trades = bt.run()._trades
        self.assertEqual(EURUSD.Close[trades["ExitTime"]].tolist(), trades["ExitPrice"].tolist())

    def test_sl_always_before_tp(self):
        class S(_S):
            def next(self):
                i = len(self.data.index)
                if i == 4:
                    self.buy(
                        qty=equity_fraction(
                            0.95,
                            account=self.account,
                            reference_price=self.close[-1],
                            instrument=self.instrument,
                        ).qty
                    )
                if i == 5:
                    t = self.trades[0]
                    t.sl = 105
                    t.tp = 107.9

        trades = Backtest(SHORT_DATA, S).run()._trades
        self.assertEqual(trades["ExitPrice"].iloc[0], 104.95)

    def test_stop_entry_and_tp_in_same_bar(self):
        class S(_S):
            def next(self):
                i = len(self.data.index)
                if i == 3:
                    self.sell(stop=108, tp=105, sl=113, qty=1)

        trades = Backtest(SHORT_DATA, S).run()._trades
        self.assertEqual(trades["ExitBar"].iloc[0], 4)
        self.assertEqual(trades["ExitPrice"].iloc[0], 104.96)  # 下一根开盘改善

    def test_optimize_datetime_index_with_timezone(self):
        data: pd.DataFrame = GOOG.iloc[:100]
        data.index = data.index.tz_localize("Asia/Kolkata")
        res = Backtest(data, SmaCross).optimize(fast=range(2, 3), slow=range(4, 5))
        self.assertGreater(res["# Trades"], 0)

    def test_optimize_range_index(self):
        # Data is passed to the workers through shared memory sized by
        # `.nbytes`, which a lazy RangeIndex under-reports, previously raising
        # "TypeError: buffer is too small for requested array". See GH issue #1237.
        data: pd.DataFrame = GOOG.iloc[:100].reset_index(drop=True)
        with self.assertWarnsRegex(UserWarning, "index is not datetime"):
            bt = Backtest(data, SmaCross)
        res = bt.optimize(fast=range(2, 3), slow=range(4, 5))
        self.assertGreater(res["# Trades"], 0)

    def test_sl_tp_values_in_trades_df(self):
        class S(_S):
            def next(self):
                self.next = lambda: None
                self.buy(qty=1, tp=111)
                self.buy(qty=1, sl=99)

        trades = Backtest(SHORT_DATA, S).run()._trades
        self.assertEqual(trades["SL"].fillna(0).tolist(), [0, 99])
        self.assertEqual(trades["TP"].fillna(0).tolist(), [111, 0])

    def test_sl_value_in_trades_df_when_gapped_through(self):
        # An SL that is gapped through (the bar opens beyond the stop, so the
        # fill price is worse than the stop price) must still be recorded in
        # stats._trades["SL"]. See GH issue #1340.
        class S(_S):
            def next(self):
                if len(self.data.index) == 9:
                    self.buy(qty=1, sl=99.5)

        trades = Backtest(SHORT_DATA, S).run()._trades
        self.assertEqual(len(trades), 1)
        trade = trades.iloc[0]
        # The long SL (99.5) is gapped through on the next bar's open, so the
        # trade exits at that worse market price rather than at the stop price.
        self.assertEqual(trade["ExitPrice"], 99.19)
        # ... yet the SL value must be preserved in the trades data frame.
        self.assertEqual(trade["SL"], 99.5)
