"""Direction, scale, and no-lookahead boundaries for composed strategies and time resampling."""

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_series_equal
from test_engine_edges import Idle, flat_data

from openbacktesting import Backtest
from openbacktesting.lib import (
    FractionalBacktest,
    SignalStrategy,
    TrailingStrategy,
    compute_stats,
    quantile,
    random_ohlc_data,
    resample_apply,
)


def test_empty_quantile_and_invalid_ohlc():
    assert np.isnan(quantile([]))
    with pytest.raises(ValueError, match="columns 'Open', 'High', 'Low', 'Close'"):
        next(random_ohlc_data(pd.DataFrame({"Close": [1, 2]})))


def test_recompute_all_trades_preserves_equity_and_returns():
    class BuyHold(Idle):
        def next(self):
            if len(self.data) == 2:
                self.buy(qty=2)
            elif len(self.data) == 5:
                self.position.close()

    data = flat_data()
    stats = Backtest(data, BuyHold).run()
    recomputed = compute_stats(stats=stats, data=data)
    for key in ["# Trades", "Equity Final [$]", "Return [%]", "Exposure Time [%]"]:
        assert recomputed[key] == stats[key]
    assert_series_equal(recomputed["_equity_curve"].Equity, stats["_equity_curve"].Equity)


@pytest.mark.parametrize("as_numpy", [True, False])
def test_resample_custom_aggregation_has_no_lookahead(as_numpy):
    series = pd.Series(range(1, 9), index=pd.date_range("2025-01-01", periods=8, freq="h"))

    def indicator(resampled):
        return resampled.to_numpy() if as_numpy else resampled

    result = resample_apply("2h", indicator, series, agg="sum")
    np.testing.assert_allclose(result.to_numpy(), [np.nan, np.nan, 3, 3, 7, 7, 11, 11])
    assert result.index.equals(series.index)


@pytest.mark.parametrize("exit_sign", [1, -1])
def test_signal_exit_closes_only_matching_direction(exit_sign):
    class Signals(SignalStrategy):
        def init(self):
            super().init()
            self.set_signal(
                [0, 2, -2, 0, 0, 0, 0, 0],
                [0, 0, 0, exit_sign * 0.5, exit_sign, -exit_sign, 0, 0],
            )

    stats = Backtest(flat_data(), Signals, hedging=True).run()
    trades = stats["_trades"]
    assert trades.Size.tolist() == [exit_sign, exit_sign, -exit_sign * 2]
    assert trades.ExitBar.tolist() == [4, 5, 6]
    assert stats["Equity Final [$]"] == 10_000
    assert not stats["_strategy"].trades


def test_signal_without_exit_vector_keeps_trade_until_finalization():
    class EntryOnly(SignalStrategy):
        def init(self):
            self.set_signal([0, -1, 0, 0, 0, 0, 0, 0])

    stats = Backtest(flat_data(), EntryOnly, end_policy="close_at_last_close").run()
    assert stats["_trades"].Size.tolist() == [-1]
    assert stats["_trades"].ExitBar.tolist() == [7]


def test_short_trailing_stop_never_moves_away_from_price():
    observed = []

    class ShortTrail(TrailingStrategy):
        def init(self):
            super().init()
            self.set_atr_periods(2)
            self.set_trailing_sl(2)

        def next(self):
            super().next()
            if len(self.data) == 2:
                self.sell(qty=1)
            for trade in self.trades:
                observed.append(trade.sl)

    data = flat_data()
    for column in ["Open", "High", "Low", "Close"]:
        data[column] -= np.arange(len(data))
    stats = Backtest(data, ShortTrail, end_policy="close_at_last_close").run()
    assert observed == [102, 101, 100, 99, 98, 97]
    assert stats["_trades"].Size.tolist() == [-1]
    assert stats["_trades"].PnL.iloc[0] > 0


def test_fractional_migration_keeps_native_indicators():
    from openbacktesting.broker import InstrumentSpec

    class Indicators(Idle):
        def init(self):
            self.price = self.ind(lambda: self.data.Close, name="price")
            self.oscillator = self.ind(lambda: np.arange(len(self.data)), name="osc")

    data = flat_data()
    with pytest.raises(TypeError, match="InstrumentSpec"):
        FractionalBacktest(data, Indicators, fractional_unit=0.01)
    result = Backtest(data, Indicators, instrument=InstrumentSpec(quantity_step=0.01)).run()
    price, oscillator = result["_strategy"]._indicators
    np.testing.assert_allclose(price, data.Close)
    np.testing.assert_array_equal(price, result["_strategy"].price)
    np.testing.assert_array_equal(oscillator, np.arange(8))
