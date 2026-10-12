"""Boundary regressions for native engine input, indicators, matching, and optimization."""

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from openbacktesting import Backtest, Strategy
from openbacktesting.strategy.sizing import equity_fraction
from openbacktesting.test import GOOG


class Idle(Strategy):
    parameter = 1

    def init(self):
        pass

    def next(self):
        pass


def flat_data(count=8):
    return pd.DataFrame(
        {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 10},
        index=pd.date_range("2025-01-01", periods=count),
    )


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"strategy": object}, "Strategy sub-type"),
        ({"strategy": None}, "Strategy sub-type"),
        ({"spread": "0.1"}, "spread"),
        ({"commission": []}, "commission"),
    ],
)
def test_backtest_rejects_invalid_types(kwargs, message):
    with pytest.raises(TypeError, match=message):
        Backtest(GOOG.iloc[:10], **({"strategy": Idle} | kwargs))


def test_unsorted_input_is_rejected_without_mutating_caller():
    data = GOOG.iloc[:10].iloc[::-1].copy()
    original = data.copy()
    with pytest.raises(ValueError, match="increasing and unique"):
        Backtest(data, Idle)
    assert_frame_equal(data, original)


@pytest.mark.parametrize("value", [None, 3, np.zeros(3), np.zeros((2, 2, 8))])
def test_indicator_rejects_invalid_shape(value):
    class BadIndicator(Idle):
        def init(self):
            self.ind(lambda: value, name="bad")

    with pytest.raises(ValueError, match="Indicators must return"):
        Backtest(flat_data(), BadIndicator).run()


def test_indicator_preserves_exception_cause():
    failure = ArithmeticError("indicator failure")

    class BadIndicator(Idle):
        def init(self):
            def broken():
                raise failure

            self.ind(broken, name="broken")

    with pytest.raises(RuntimeError, match='Indicator "broken" error') as caught:
        Backtest(flat_data(), BadIndicator).run()
    assert caught.value.__cause__ is failure


def test_dataframe_indicator_keeps_column_order():
    data = flat_data()

    class FrameIndicator(Idle):
        def init(self):
            self.lines = self.ind(lambda: data[["High", "Low"]], name=["high", "low"])

    strategy = Backtest(data, FrameIndicator).run()["_strategy"]
    np.testing.assert_array_equal(strategy.lines, data[["High", "Low"]].to_numpy().T)
    assert strategy.lines.name == ["high", "low"]


def test_repr_exposes_order_position_and_trade_state():
    class Inspect(Idle):
        def next(self):
            if len(self.data) == 2:
                order = self.buy(qty=2, sl=90, tp=110, tag="entry")
                assert "size=2" in repr(order) and "tag='entry'" in repr(order)
            if len(self.data) == 3:
                assert "2 (1 trades)" in repr(self.position)
                assert "size=2" in repr(self.trades[0])
                assert "tag=entry" in repr(self.trades[0])
                assert "(1 trades)" in repr(self._broker)
                self.position.close()

    result = Backtest(flat_data(), Inspect).run()
    assert repr(result["_strategy"]) == "<Strategy Inspect>"
    assert not hasattr(Strategy, "_FULL_EQUITY")
    assert result["# Trades"] == 1


def test_short_order_rejects_inverted_bracket():
    class BadShort(Idle):
        def next(self):
            self.sell(qty=1, sl=90, tp=110)

    with pytest.raises(ValueError, match="SL direction"):
        Backtest(flat_data(), BadShort).run()


def test_tiny_equity_budget_returns_zero_without_order():
    class TinyOrder(Idle):
        def next(self):
            if len(self.data) == 2:
                decision = equity_fraction(
                    0.001, account=self.account, reference_price=self.close[-1]
                )
                assert decision.qty == 0 and decision.reason == "below_min_quantity"

    stats = Backtest(flat_data(), TinyOrder).run()
    assert stats["# Trades"] == 0
    assert stats["Equity Final [$]"] == 10_000
    assert stats["_orders"].empty


def test_partial_close_resizes_brackets_then_clears_them():
    class Partial(Idle):
        def next(self):
            if len(self.data) == 2:
                self.buy(qty=4, sl=90, tp=110)
            elif len(self.data) == 3:
                self.trades[0].close(0.5)
            elif len(self.data) == 4:
                trade = self.trades[0]
                assert trade.size == 2
                assert {o.size for o in self.orders} == {-2}
                assert len(self.orders) == 2
                trade.sl = None
                trade.tp = None
                assert trade.sl is trade.tp is None
                assert not self.orders
                trade.close()

    stats = Backtest(flat_data(), Partial).run()
    assert stats["_trades"]["Size"].tolist() == [2, 2]
    assert stats["_trades"]["ExitBar"].tolist() == [3, 4]
    assert stats["Equity Final [$]"] == 10_000


def test_exclusive_order_cancels_pending_entry_and_closes_bracketed_trade():
    class Exclusive(Idle):
        def next(self):
            if len(self.data) == 2:
                old = self.buy(qty=1, limit=80)
                self.buy(qty=2, sl=90, tp=110)
                assert old not in self.orders
            elif len(self.data) == 3:
                self.sell(qty=1)
            elif len(self.data) == 4:
                assert len(self.trades) == 1 and self.trades[0].size == -1
                assert not self.orders
                self.position.close()

    stats = Backtest(flat_data(), Exclusive, exclusive_orders=True).run()
    assert stats["_trades"]["Size"].tolist() == [2, -1]


def test_netting_order_closes_multiple_trades_fifo():
    class Netting(Idle):
        def next(self):
            if len(self.data) == 2:
                self.buy(qty=1, tag="first")
                self.buy(qty=2, tag="second")
            elif len(self.data) == 3:
                self.sell(qty=4, tag="remainder")
            elif len(self.data) == 4:
                assert [t.size for t in self.trades] == [-1]
                self.position.close()

    stats = Backtest(flat_data(), Netting).run()
    assert stats["_trades"]["Size"].tolist() == [1, 2, -1]
    assert stats["_trades"]["Tag"].tolist() == ["first", "second", "remainder"]


def test_optimizer_rejects_unknown_method():
    with pytest.raises(ValueError, match="Method should be"):
        Backtest(flat_data(), Idle).optimize(parameter=[1, 2], method="unknown")


@pytest.mark.parametrize("method", ["sambo", "skopt"])
def test_sambo_float_bounds_and_deprecated_alias(method):
    bt = Backtest(flat_data(), Idle)
    kwargs = {"parameter": [0.1, 0.9], "max_tries": 5, "random_state": 42}
    if method == "skopt":
        with pytest.warns(DeprecationWarning, match="deprecated"):
            stats = bt.optimize(method=method, **kwargs)
    else:
        stats = bt.optimize(method=method, **kwargs)
    assert 0.1 <= stats["_strategy"].parameter <= 0.9
    assert stats["# Trades"] == 0


def test_sambo_timedelta_bounds_and_constrained_grid_size():
    stats = Backtest(flat_data(), Idle).optimize(
        parameter=[np.timedelta64(1, "D"), np.timedelta64(3, "D")],
        method="sambo",
        max_tries=5,
        random_state=42,
    )
    assert 1 <= stats["_strategy"].parameter < 4
    stats, heatmap = Backtest(flat_data(), Idle).optimize(
        parameter=[1, 2, 3],
        constraint=lambda p: p.parameter > 1,
        max_tries=2,
        return_heatmap=True,
        random_state=42,
    )
    assert list(heatmap.index) == [(2,), (3,)]
    assert stats["_strategy"].parameter == 2


def test_large_grid_warns_and_returns_all_parameter_scores(monkeypatch):
    from test_modularization import InlinePool

    import openbacktesting

    monkeypatch.setattr(openbacktesting, "Pool", lambda: InlinePool([]))
    with pytest.warns(UserWarning, match="Searching for best of 301 configurations"):
        stats, scores = Backtest(flat_data(), Idle).optimize(
            parameter=range(301), return_heatmap=True, random_state=42
        )
    assert len(scores) == 301
    assert scores.index.tolist() == [(i,) for i in range(301)]
    assert scores.isna().all()  # Combinations without trades must not produce spurious scores.
    assert stats["_strategy"].parameter == 0
    assert stats["# Trades"] == 0
