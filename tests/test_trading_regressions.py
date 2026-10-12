"""交易核心研究探针：使用人工预期验证因果性、费用与暴露。"""

import pandas as pd
import pytest
from openbacktesting import Backtest, Strategy
from openbacktesting.lib import TrailingStrategy


def prices():
    return pd.DataFrame(
        {
            "Open": [100, 100, 100, 110, 120, 125],
            "High": [101, 101, 111, 121, 131, 151],
            "Low": [99, 99, 99, 109, 119, 124],
            "Close": [100, 100, 110, 120, 130, 150],
            "Volume": [1000] * 6,
        },
        index=pd.date_range("2026-01-01", periods=6),
    )


class Hold(Strategy):
    def init(self):
        pass

    def next(self):
        if len(self.data) == 2:
            self.buy(qty=2)


def test_terminal_exit_uses_last_close():
    result = Backtest(prices(), Hold, end_policy="close_at_last_close").run()
    assert result["Equity Final [$]"] == 10100
    assert result._trades.iloc[0].ExitPrice == 150


@pytest.mark.parametrize("finalize", [False, True])
def test_terminal_does_not_execute_new_entry(finalize):
    class LastBar(Hold):
        def next(self):
            if len(self.data) == 6:
                self.buy(qty=2)

    result = Backtest(
        prices(), LastBar, end_policy="close_at_last_close" if finalize else "mark_to_market"
    ).run()
    assert result["Equity Final [$]"] == 10000
    assert not result._strategy.trades
    assert not result._strategy.orders


def test_open_position_contributes_to_exposure():
    result = Backtest(prices(), Hold).run()
    assert result["Exposure Time [%]"] == pytest.approx(100 * 4 / 6)
    assert result["Equity Final [$]"] == 10100
    assert result._trades.empty


def test_partial_exits_allocate_actual_entry_fee_once():
    frame = prices().assign(Open=100, High=101, Low=99, Close=100)

    class Split(Hold):
        def next(self):
            if len(self.data) == 2:
                self.buy(qty=10)
            elif len(self.data) == 3:
                self.trades[0].close(0.5)
            elif len(self.data) == 4:
                self.trades[0].close()

    result = Backtest(frame, Split, commission=(5, 0)).run()
    assert result["Equity Final [$]"] == 9985
    assert list(result._trades.Commission) == [7.5, 7.5]
    assert result._trades.PnL.sum() == -15


@pytest.mark.parametrize("mode", ["atr", "percent"])
def test_trailing_history_does_not_depend_on_future(mode):
    class Trailing(TrailingStrategy):
        def init(self):
            super().init()
            self.set_atr_periods(4)
            if mode == "atr":
                self.set_trailing_sl(1)
            else:
                self.set_trailing_pct(0.05)
            self.observed = None

        def next(self):
            super().next()
            if len(self.data) == 2:
                self.buy(qty=1)
            if len(self.data) == 3:
                self.observed = self.trades[0].sl

    observed = []
    for high, low in [(101, 99), (110, 90)]:
        frame = pd.DataFrame(
            {
                "Open": 100,
                "Close": 100,
                "High": [101] * 4 + [high] * 3,
                "Low": [99] * 4 + [low] * 3,
                "Volume": 1000,
            },
            index=pd.date_range("2026-01-01", periods=7),
        )
        observed.append(Backtest(frame, Trailing).run()._strategy.observed)
    assert observed == ([None, None] if mode == "atr" else [95, 95])


@pytest.mark.parametrize(
    "entry,expected",
    [({}, 100), ({"limit": 99}, 99), ({"stop": 101}, 101), ({"stop": 101, "limit": 102}, 101)],
)
def test_zero_cost_entry_baseline(entry, expected):
    class Entry(Hold):
        def next(self):
            if len(self.data) == 2:
                self.buy(qty=2, **entry)
            if len(self.data) == 3:
                self.position.close()

    result = Backtest(prices(), Entry).run()
    assert len(result._trades) == 1
    trade = result._trades.iloc[0]
    assert (trade.EntryBar, trade.EntryPrice, trade.Size) == (2, expected, 2)
    assert (trade.ExitBar, trade.ExitPrice) == (3, 110)


def test_fifo_and_bracket_baseline():
    class Lots(Hold):
        def next(self):
            if len(self.data) == 2:
                self.buy(qty=2, sl=90, tp=200, tag="first")
                self.buy(qty=1, tag="second")
            if len(self.data) == 3:
                self.sell(qty=3)

    result = Backtest(prices(), Lots).run()
    assert list(result._trades.Tag) == ["first", "second"]
    assert list(result._trades.Size) == [2, 1]
    assert not result._strategy.orders
    assert result["Equity Final [$]"] == 10030
