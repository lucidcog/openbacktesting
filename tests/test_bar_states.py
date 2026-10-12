"""首根执行、状态生命周期和首根资金基准的可观察契约。"""

import pickle
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest
from openbacktesting import Backtest, BarState
from openbacktesting.indicators.types import IndicatorHandle
from openbacktesting.inputs import InputError
from openbacktesting.lib import compute_stats
from openbacktesting.strategy import BarState as StrategyBarState
from test_engine_edges import Idle, flat_data


def unavailable(owner):
    for name in ("bar_index", "bar_state"):
        with pytest.raises(RuntimeError, match="不存在当前执行 bar"):
            getattr(owner, name)


def test_frozen_state_exports_and_pickle():
    assert BarState is StrategyBarState
    state = BarState(True, False)
    assert pickle.loads(pickle.dumps(state)) == state
    with pytest.raises(FrozenInstanceError):
        state.is_first = False


@pytest.mark.parametrize("count", [1, 6])
@pytest.mark.parametrize("values", ["missing", "gaps", "none"])
def test_every_bar_and_lifecycle(count, values):
    records, saved = [], []

    class Observe(Idle):
        def init(self):
            unavailable(self)
            self.full_index = self.data_index
            if values != "none":
                array = np.full(count, np.nan)
                if values == "gaps":
                    array[2:4] = 2
                self.ind(lambda: array)

        def on_start(self):
            assert self.bar_index == 0
            assert self.bar_state == BarState(True, count == 1)

        def next(self):
            i = self.bar_index
            assert len(self.data_index) == len(self.close) == i + 1
            assert len(self.full_index) == count
            records.append(i)
            saved.append(self.bar_state)
            assert self.bar_state == BarState(i == 0, i == count - 1)
            if i == 0:
                with pytest.raises(IndexError):
                    _ = self.close[-2]

        def on_finish(self, summary):
            unavailable(self)
            assert summary.reason == "end_of_data"

    bt = Backtest(flat_data(count), Observe)
    owner = bt.run()["_strategy"]
    assert records == list(range(count))
    assert saved[0] == BarState(True, count == 1)
    unavailable(owner)
    records.clear()
    bt.run()
    assert records == list(range(count))


@pytest.mark.parametrize("stage", ["init", "start", "next", "order", "fill", "finish"])
def test_exception_clears_current_state(stage):
    owners = []

    class Fail(Idle):
        def init(self):
            owners.append(self)
            if stage == "init":
                raise ValueError(stage)

        def on_start(self):
            if stage == "start":
                raise ValueError(stage)

        def next(self):
            if stage == "next":
                raise ValueError(stage)
            if self.bar_state.is_first:
                self.buy(qty=1)

        def on_order(self, event):
            if stage == "order":
                raise ValueError(stage)

        def on_fill(self, event):
            if stage == "fill":
                raise ValueError(stage)

        def on_finish(self, summary):
            unavailable(self)
            if stage == "finish":
                raise ValueError(stage)

    with pytest.raises(ValueError, match=stage):
        Backtest(flat_data(3), Fail, execution_timing="same_close").run()
    unavailable(owners[0])


@pytest.mark.parametrize("name", ["bar_state", "bar_index", "data_index"])
def test_new_names_reserved(name):
    from test_fluent_indicators import strategy

    for value in (1, lambda self: 0, property(lambda self: 0)):
        base = type("ConflictBase", (Idle,), {name: value})
        cls = type("Child", (base,), {})
        with pytest.raises(InputError, match=name):
            Backtest(flat_data(), cls).run()
        with pytest.raises(AttributeError, match=name):
            cls(None, strategy(flat_data()).data, {})
    owner = strategy(flat_data())
    with pytest.raises(AttributeError, match=name):
        setattr(owner, name, 2)
    with pytest.raises(AttributeError, match=name):
        delattr(owner, name)
    with pytest.raises(AttributeError, match=name):
        Backtest(flat_data(), Idle).run(**{name: 2})


def test_index_labels_are_not_positions():
    records = []

    class Labels(Idle):
        def next(self):
            with pytest.raises(AttributeError):
                _ = self.index
            records.append((self.bar_index, self.data_index[-1]))
            assert self.data_index.equals(self.data.index)

    data = flat_data(3)
    data.index = pd.RangeIndex(100, 103)
    Backtest(data, Labels).run()
    assert records == [(0, 100), (1, 101), (2, 102)]

    class Custom(Idle):
        index = 3

    assert Backtest(data, Custom).run(index=7)["_strategy"].index == 7


def test_removed_warmup_and_diagnostic_readiness():
    from test_fluent_indicators import strategy

    owner = strategy(flat_data())
    called = []
    with pytest.raises(TypeError, match="warmup"):
        owner.ind(lambda **kwargs: called.append(kwargs), warmup=False)
    assert not called
    with pytest.raises(TypeError, match="warmup"):
        IndicatorHandle([1], name="x", index=pd.RangeIndex(1), warmup=False)
    handle = owner.ind(lambda: [np.nan, 1, 2, np.nan, 4, 5, 6, 7])
    assert handle.first_ready() == 1
    assert not handle.ready_at(0) and handle.ready_at(1)
    assert "warmup" not in handle.metadata and "warmup" not in handle._opts


class FirstEntry(Idle):
    def next(self):
        if self.bar_state.is_first:
            self.buy(qty=1)


@pytest.mark.parametrize("timing, entry", [("next_open", 1), ("same_close", 0)])
def test_first_entry_and_notification_positions(timing, entry):
    events = []

    class Observe(FirstEntry):
        def on_order(self, event):
            events.append((self.bar_index, self.bar_state, event.bar_index))

        def on_fill(self, event):
            events.append((self.bar_index, self.bar_state, event.bar_index))

    result = Backtest(flat_data(3), Observe, execution_timing=timing).run()
    assert result["_fills"].iloc[0].bar_index == entry
    assert all(i == event_i and state == BarState(i == 0, i == 2) for i, state, event_i in events)


@pytest.mark.parametrize("policy", ["mark_to_market", "close_at_last_close"])
def test_single_bar_next_open_never_fills(policy):
    result = Backtest(flat_data(1), FirstEntry, end_policy=policy).run()
    assert result["_fills"].empty
    assert result["Equity Final [$]"] == 10000


def test_first_bar_fee_and_recalculation():
    data = flat_data(1)
    result = Backtest(
        data, FirstEntry, cash=1000, commission=(10, 0), execution_timing="same_close"
    ).run()
    assert result.attrs["statistics_initial_equity"] == 1000
    assert result["Equity Final [$]"] == 990
    assert result["Equity Peak [$]"] == 1000
    assert result["Return [%]"] == -1
    assert result["Max. Drawdown [%]"] == pytest.approx(-1)
    assert result["Avg. Drawdown [%]"] == pytest.approx(-1)
    assert result["Max. Drawdown Duration"] == pd.Timedelta(0)
    assert np.isnan(result["CAGR [%]"])
    assert len(result["_equity_curve"]) == 1
    again = compute_stats(stats=result, data=data)
    for key in ("Return [%]", "Max. Drawdown [%]", "Buy & Hold Return [%]"):
        assert again[key] == result[key]
    empty = compute_stats(stats=result, data=data, trades=result["_trades"].iloc[:0])
    assert empty["Return [%]"] == 0
    assert empty["Equity Final [$]"] == 1000
    assert result["Equity Final [$]"] == 990
    legacy = result.copy()
    del legacy.attrs["statistics_initial_equity"]
    assert compute_stats(stats=legacy, data=data)["Return [%]"] == 0


@pytest.mark.parametrize("value", [0, -1, np.nan, np.inf, None, True, "1000"])
def test_recalculation_rejects_bad_initial_equity(value):
    result = Backtest(flat_data(), Idle).run()
    result.attrs["statistics_initial_equity"] = value
    with pytest.raises((TypeError, ValueError), match="initial_equity"):
        compute_stats(stats=result, data=flat_data())


def test_first_period_fee_in_annualized_returns():
    result = Backtest(
        flat_data(2), FirstEntry, cash=1000, commission=(10, 0), execution_timing="same_close"
    ).run()
    assert result["Return (Ann.) [%]"] == pytest.approx((0.99 ** (252 / 2) - 1) * 100)


def test_buy_and_hold_ignores_missing_indicator():
    class Missing(Idle):
        def init(self):
            self.ind(lambda: [np.nan] * 3)

    data = flat_data(3)
    data.loc[data.index[-1], ["Open", "High", "Low", "Close"]] = 120
    assert Backtest(data, Missing).run()["Buy & Hold Return [%]"] == 20


def test_insolvency_terminal_context_is_not_input_last():
    seen, terminal = [], []

    class Insolvent(FirstEntry):
        def next(self):
            seen.append(self.bar_index)
            if self.bar_state.is_first:
                self.buy(qty=10)

        def on_order(self, event):
            if event.phase == "terminal":
                terminal.append((self.bar_index, self.bar_state))

        def on_fill(self, fill):
            if fill.phase == "terminal":
                terminal.append((self.bar_index, self.bar_state))

        def on_finish(self, summary):
            assert summary.reason == "insolvent"
            unavailable(self)

    data = flat_data(4)
    data.iloc[1:, :4] = 1
    result = Backtest(data, Insolvent, cash=100, margin=0.1, execution_timing="same_close").run()
    assert seen == [0]
    assert terminal and all(pair == (1, BarState(False, False)) for pair in terminal)
    unavailable(result["_strategy"])


def test_primary_and_finish_errors_keep_context_closed():
    class Failed(Idle):
        def next(self):
            assert self.bar_state.is_first
            raise ValueError("primary")

        def on_finish(self, summary):
            unavailable(self)
            raise RuntimeError("secondary")

    with pytest.raises(ValueError, match="primary") as info:
        Backtest(flat_data(), Failed).run()
    assert "secondary" in str(info.value.__notes__)


@pytest.mark.parametrize("name", ["bar_index", "bar_state", "data_index"])
def test_input_binding_rejected_but_display_title_allowed(name):
    from openbacktesting import inputs

    conflict = type("Conflict", (Idle,), {name: inputs.int(2, title="参数")})
    with pytest.raises(InputError, match=name):
        Backtest(flat_data(), conflict).run()
    allowed = type("Allowed", (Idle,), {"period": inputs.int(2, title=name)})
    assert Backtest(flat_data(), allowed).run()["_strategy"].period == 2


def test_first_drawdown_recovery_and_intraday_periods():
    from openbacktesting.portfolio.stats import compute_drawdown_duration_peaks
    from openbacktesting.portfolio.stats import compute_stats as raw_stats

    index = pd.date_range("2026-01-05", periods=4, freq="12h")
    dd = pd.Series(
        [0.01, 0.02, 0.0, 0.03, 0.03], index=pd.date_range(index[0], periods=5, freq="12h")
    )
    durations, peaks = compute_drawdown_duration_peaks(dd)
    assert durations.iloc[2] == pd.Timedelta("1 day")
    assert durations.iloc[4] == pd.Timedelta("1 day")
    assert peaks.iloc[2] == 0.02 and peaks.iloc[4] == 0.03
    data = flat_data(4)
    data.index = index
    data["Close"] = [100, 101, 102, 103]
    base = Backtest(data, Idle).run()
    equity = np.array([990.0, 995.0, 1000.0, 1010.0])
    result = raw_stats(base["_trades"], equity, data, None, initial_equity=1000)
    assert result["Return (Ann.) [%]"] == pytest.approx((1.01 ** (252 / 2) - 1) * 100)
    assert result["Beta"] == pytest.approx(
        np.cov(np.log(equity[1:] / equity[:-1]), np.log([1.01, 102 / 101, 103 / 102]))[0, 1]
        / np.var(np.log([1.01, 102 / 101, 103 / 102]), ddof=1)
    )
    assert result["CAGR [%]"] == pytest.approx((1.01 ** (365.25 / 1.5) - 1) * 100)


def test_notification_orders_wait_and_first_bar_protection():
    class Protective(FirstEntry):
        def next(self):
            if self.bar_state.is_first:
                self.buy(qty=1, sl=95)

        def on_fill(self, fill):
            if fill.bar_index == 0:
                self.buy(qty=1)

    data = flat_data(3)
    data.iloc[0, data.columns.get_loc("Low")] = 90
    data.iloc[1, data.columns.get_loc("Low")] = 90
    result = Backtest(data, Protective, execution_timing="same_close").run()
    fills = result["_fills"]
    assert list(fills.bar_index) == [0, 1, 1]
    assert fills.iloc[0].price == 100 and fills.iloc[1].price == 95


def test_signal_template_uses_first_signal_and_ignores_missing():
    from openbacktesting.lib import SignalStrategy

    class Signals(SignalStrategy):
        def init(self):
            super().init()
            self.set_signal([1.0, np.nan, 0.0, -1.0])

    result = Backtest(flat_data(4), Signals, execution_timing="same_close").run()
    assert list(result["_fills"].bar_index) == [0, 3]
    assert result["_trades"].iloc[0].EntryBar == 0
    assert result["_trades"].iloc[0].ExitBar == 3
