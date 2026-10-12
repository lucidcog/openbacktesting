"""已关闭片段的费用口径、冻结、阶段与运行隔离。"""

import pickle
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest
from openbacktesting import Backtest, Strategy, inputs
from openbacktesting.broker import ClosedTradeStats, Commission
from openbacktesting.inputs import InputError


def data(prices=(100.0, 112.0, 98.0, 102.0, 100.0)):
    return pd.DataFrame(
        {
            "Open": prices,
            "High": np.array(prices) + 1,
            "Low": np.array(prices) - 1,
            "Close": prices,
            "Volume": [100.0] * len(prices),
        },
        index=pd.date_range("2026-01-01", periods=len(prices)),
    )


class Partial(Strategy):
    def init(self):
        self.snapshots = [("init", self.closed_trade_stats)]

    def on_start(self):
        self.snapshots.append(("start", self.closed_trade_stats))

    def next(self):
        if self.bar_index == 0:
            self.buy(qty=3)
        if self.bar_index in (1, 2, 3):
            self.trades[0].close(qty=1)
        self.snapshots.append(("next", self.closed_trade_stats))

    def on_order(self, event):
        self.snapshots.append(("order", self.closed_trade_stats))

    def on_fill(self, event):
        self.snapshots.append(("fill", self.closed_trade_stats))

    def on_finish(self, summary):
        self.snapshots.append(("finish", self.closed_trade_stats))


def test_partial_fees_frozen_and_same_close_visibility():
    bt = Backtest(data(), Partial, commission=Commission(per_unit=1), execution_timing="same_close")
    a = bt.run()["_strategy"]
    s = a.closed_trade_stats
    assert s == ClosedTradeStats(3, 1, 1, 1, 10.0, 4.0, 6.0, 2.0, 1 / 3)
    assert len({t.trade_id for t in a.closed_trades}) == 1
    assert sum(t.pl for t in a.closed_trades) == s.net_profit
    assert pickle.loads(pickle.dumps(s)) == s
    with pytest.raises(FrozenInstanceError):
        s.net_profit = 99
    assert a.snapshots[0][1] == ClosedTradeStats()
    assert [x.closed_count for phase, x in a.snapshots if phase == "next"] == [0, 0, 1, 2, 3]
    assert a.snapshots[-1] == ("finish", s)
    assert [x.closed_count for phase, x in a.snapshots if phase == "fill"] == [0, 1, 2, 3]
    a.closed_trades[0].exit_price = 999
    assert a.closed_trade_stats == s

    class NoScan(list):
        def __iter__(self):
            raise AssertionError("查询不应扫描历史")

    a._broker.closed_trades = NoScan(a._broker.closed_trades)
    assert a.closed_trade_stats == s
    b = bt.run()["_strategy"]
    assert b.snapshots[0][1] == ClosedTradeStats() and b.closed_trade_stats == s


@pytest.mark.parametrize("hedging", [False, True])
@pytest.mark.parametrize("fee", [1.0, -1.0])
def test_reversal_hedging_rebate_and_terminal(hedging, fee):
    class Reversal(Strategy):
        def init(self):
            pass

        def next(self):
            if self.bar_index == 0:
                self.buy(qty=1)
            if self.bar_index == 1:
                self.sell(qty=2)

        def on_finish(self, summary):
            self.final = self.closed_trade_stats

    r = Backtest(
        data(),
        Reversal,
        hedging=hedging,
        commission=lambda qty, price: abs(qty) * fee,
        execution_timing="same_close",
        end_policy="close_at_last_close",
    ).run()
    o = r["_strategy"]
    pieces = o.closed_trades
    s = o.closed_trade_stats
    assert s == o.final
    assert s.closed_count == len(pieces) > 0
    assert s.net_profit == pytest.approx(sum(t.pl for t in pieces))
    assert s.winning_profit == pytest.approx(sum(max(t.pl, 0) for t in pieces))
    assert s.losing_amount == pytest.approx(sum(max(-t.pl, 0) for t in pieces))


def test_open_cost_empty_and_failure_preserves_completed_facts():
    owners = []

    class Fails(Partial):
        def init(self):
            super().init()
            owners.append(self)

        def next(self):
            super().next()
            if self.bar_index == 1:
                assert self.account.fees_paid > 0
                assert self.closed_trade_stats == ClosedTradeStats()
            if self.bar_index == 2:
                raise ValueError("stop")

    with pytest.raises(ValueError, match="stop"):
        Backtest(
            data(), Fails, commission=Commission(per_unit=1), execution_timing="same_close"
        ).run()
    assert owners[0].closed_trade_stats.closed_count == 1
    assert owners[0].closed_trade_stats.net_profit == 10


def test_reserved_name_all_entrypoints():
    from test_fluent_indicators import strategy

    for value in (1, lambda self: 0, property(lambda self: 0), inputs.int(1, title="另一个标题")):
        conflict = type("Conflict", (Partial,), {"closed_trade_stats": value})
        with pytest.raises(InputError, match="closed_trade_stats"):
            Backtest(data(), conflict).run()
        with pytest.raises(AttributeError, match="closed_trade_stats"):
            conflict(None, strategy(data()).data, {})
    with pytest.raises(AttributeError, match="closed_trade_stats"):
        Backtest(data(), Partial).run(closed_trade_stats=1)

    class Title(Strategy):
        n = inputs.int(1, title="closed_trade_stats")

        def init(self):
            pass

        def next(self):
            pass

    owner = Backtest(data(), Title).run()["_strategy"]
    assert owner.closed_trade_stats == ClosedTradeStats()
    with pytest.raises(AttributeError):
        owner.closed_trade_stats = ClosedTradeStats()
    with pytest.raises(AttributeError):
        del owner.closed_trade_stats


def test_multiple_exits_in_one_bar_share_entry_fee_once():
    class Batch(Strategy):
        def init(self):
            self.seen = []

        def next(self):
            if self.bar_index == 0:
                self.buy(qty=3)
            elif self.bar_index == 1:
                for _ in range(3):
                    self.trades[0].close(qty=1)

        def on_fill(self, fill):
            self.seen.append(self.closed_trade_stats)

    result = Backtest(
        data(), Batch, commission=Commission(per_unit=1), execution_timing="same_close"
    ).run()
    owner = result._strategy
    # 既有调度在批次完成后派送通知；同批三个通知读取同一最终事实。
    assert [snapshot.closed_count for snapshot in owner.seen] == [0, 3, 3, 3]
    assert owner.closed_trade_stats == ClosedTradeStats(3, 3, 0, 0, 30.0, 0.0, 30.0, 10.0, 1.0)
    assert sum(t.pl for t in owner.closed_trades) == 30.0
    assert result["Commissions [$]"] == 6.0
