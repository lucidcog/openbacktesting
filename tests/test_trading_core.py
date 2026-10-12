"""Trading policy v2: manual ledgers, causal timing, and audit records."""

import json
import pickle
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from openbacktesting import Backtest, Strategy
from openbacktesting.broker import InstrumentSpec, OrderRequest, OrderStatus, Slippage
from openbacktesting.strategy.sizing import equity_fraction, fixed_quantity, stop_risk


def frame(n=7):
    return pd.DataFrame(
        {"Open": 100.0, "High": 110.0, "Low": 90.0, "Close": 100.0},
        index=pd.date_range("2026-01-01", periods=n, tz="UTC"),
    )


class Idle(Strategy):
    def init(self):
        pass

    def next(self):
        pass


def run(actions, *, data=None, **kwargs):
    class Script(Idle):
        def next(self):
            actions(self, len(self.data) - 1)

    return Backtest(frame() if data is None else data, Script, **kwargs).run()


def test_atomic_reversal_and_fee_allocation():
    def action(s, i):
        if i == 1:
            s.buy(qty=2, tag="a")
            s.buy(qty=3, tag="b")
        if i == 2:
            s.sell(qty=7)

    result = run(action, commission=(5, 0))
    assert result._fills.qty.tolist() == [2, 3, 7]
    assert result._final_account["balance"] == 9985
    assert result._final_account["fees_paid"] == 15
    assert result._open_trades.Size.tolist() == [-2]
    assert result._trades.Size.tolist() == [2, 3]
    allocation = result._trade_allocations
    for fill in result._fills.itertuples():
        pieces = allocation[allocation.fill_id == fill.fill_id]
        assert pieces.qty.sum() == fill.qty
        assert pieces.fee.sum() == pytest.approx(fill.fee)
    assert result._trades.Commission.sum() + result._open_trades.EntryFeeRemaining.sum() == 15


@pytest.mark.parametrize(
    "options,reason",
    [
        ({"allow_short": False}, "short_not_allowed"),
        ({"cash": 1000}, "insufficient_funds"),
        ({"max_gross_exposure": 0.03}, "gross_exposure_limit"),
    ],
)
def test_rejected_reversal_has_no_partial_effect(options, reason):
    def action(s, i):
        if i == 1:
            s.buy(qty=2)
        if i == 2:
            s.sell(qty=100)

    r = run(action, commission=(5, 0), **options)
    assert r._orders.iloc[-1].reason == reason
    assert r._open_trades.Size.tolist() == [2]
    assert len(r._fills) == 1 and r["Commissions [$]"] == 5
    assert r._trades.empty


def test_reduce_only_partial_remainder_and_duplicate_exit():
    def action(s, i):
        if i == 1:
            s.buy(qty=6)
        if i == 2:
            s.sell(qty=10, reduce_only=True)
            s.close_position()

    r = run(action)
    assert r._fills.qty.tolist() == [6, 6]
    rows = r._order_events.query("order_id == 'order-2'")
    assert rows.status.tolist() == ["Submitted", "Accepted", "PartiallyFilled", "Canceled"]
    assert rows.iloc[-1].filled_qty == 6 and rows.iloc[-1].remaining_qty == 4
    assert r._orders.iloc[-1].reason == "no_position"
    assert r._open_trades.empty


def test_hedged_zero_net_has_exposure_and_separate_basis():
    def action(s, i):
        if i == 1:
            s.buy(qty=2)
            s.sell(qty=2)
        if i == 2:
            assert s.position and not s.position.is_long and not s.position.is_short
            p = s.position.snapshot
            assert p.gross_qty == 4 and p.net_qty == 0 and p.avg_price is None
            assert s.position.return_fraction is None
            assert p.long_avg_price == p.short_avg_price == 100
            with pytest.raises(ValueError, match="Hedged reduce-only orders must reference a trade"):
                s.sell(qty=1, reduce_only=True)
            with pytest.raises(ValueError, match="hedging"):
                s.order_target_quantity(target=0)
            assert len(s.close_position()) == 2

    r = run(action, hedging=True, commission=(5, 0))
    assert r["Exposure Time [%]"] == pytest.approx(100 / 7)
    assert r._final_account["balance"] == 9980
    assert r._positions.iloc[2].unrealized_pnl_net == -10


def test_frozen_requests_history_and_deterministic_ids():
    def action(s, i):
        if i == 1:
            tag = {"x": [1]}
            s.order = s.buy(qty=1, stop=105, limit=95, tag=tag)
            tag["x"].append(2)
            with pytest.raises(FrozenInstanceError):
                s.order.request.qty = 2
            with pytest.raises(AttributeError):
                s.order.order_id = "changed"
            with pytest.raises(AttributeError):
                s.order.request = None
            with pytest.raises(AttributeError):
                s.order.snapshot = None
        if i == 2:
            assert s.order.request.stop == 105 and s.order.snapshot.triggered
            assert s.order.tag == {"x": [1]}
            s.order.tag["x"].append(3)
            s.order.cancel()
            s.order.cancel()

    a, b = run(action), run(action)
    pd.testing.assert_frame_equal(a._orders, b._orders)
    sequence = sorted(a._order_events.sequence.tolist() + a._fills.sequence.tolist())
    assert sequence == list(range(1, len(sequence) + 1))
    assert a._order_events.iloc[0].status == "Submitted"
    assert not a._order_events.iloc[0].triggered


@pytest.mark.parametrize("timing,entry,exit_", [("next_open", 2, 3), ("same_close", 1, 2)])
def test_execution_phase_and_end_policy(timing, entry, exit_):
    def action(s, i):
        if i == 1:
            s.buy(qty=1)
        if i == 2:
            s.close_position()

    r = run(action, execution_timing=timing)
    assert r._fills.bar_index.tolist() == [entry, exit_]
    assert r._fills.phase.tolist() == ["execute" if timing == "next_open" else "close"] * 2


def test_callbacks_are_causal_and_not_gated_and_error_preserved():
    seen = []

    class Hooks(Idle):
        def init(self):
            self.ind(lambda: np.array([1, 1, np.nan, 1, 1, 1, 1]))

        def on_start(self):
            seen.append("start")
            with pytest.raises(RuntimeError):
                self.buy(qty=1)

        def next(self):
            if len(self.data) == 2:
                self.buy(qty=1)

        def on_order(self, event):
            seen.append(event)

        def on_fill(self, fill):
            seen.append(fill)
            if fill.side == "buy":
                self.close_position()

        def on_finish(self, summary):
            seen.append(summary.reason)
            with pytest.raises(RuntimeError):
                self.buy(qty=1)

    r = Backtest(frame(), Hooks).run()
    assert seen[0] == "start" and seen[-1] == "end_of_data"
    assert r._fills.bar_index.tolist() == [2, 3]
    failure = ValueError("primary")

    class Broken(Hooks):
        def next(self):
            raise failure

        def on_finish(self, summary):
            raise RuntimeError("secondary")

    with pytest.raises(ValueError) as caught:
        Backtest(frame(), Broken).run()
    assert caught.value is failure
    assert "secondary" in caught.value.__notes__[0]


def test_final_last_order_cancellation_and_close_costs():
    def action(s, i):
        if i in (1, 6):
            s.buy(qty=1)

    r = run(
        action,
        end_policy="close_at_last_close",
        spread=0.01,
        slippage=Slippage("fixed", 1),
        commission=(5, 0),
    )
    assert r._fills.price.tolist() == [102, 98]
    assert r._fills.iloc[-1].reason == "end_liquidation"
    assert r._orders.query("order_id == 'order-2'").iloc[0].reason == "end_of_data"
    assert r._final_account["balance"] == 9986
    assert r._positions.iloc[-2].gross_qty == 1 and r._positions.iloc[-1].gross_qty == 0
    assert r["Exposure Time [%]"] == pytest.approx(5 / 7 * 100)


def test_gap_insolvency_keeps_deficit():
    data = frame()
    data.iloc[3:] = [1, 1, 1, 1]
    r = run(lambda s, i: s.buy(qty=20) if i == 1 else None, data=data, cash=1000, margin=0.1)
    assert r._final_account["balance"] == -980
    assert r._equity_curve.Equity.iloc[-1] == -980
    assert r._fills.iloc[-1].reason == "insolvent"
    assert r._open_trades.empty


def test_open_affordability_not_future_close():
    def action(s, i):
        if i == 1:
            s.buy(qty=9)

    a = frame()
    b = frame()
    b.loc[b.index[2], "Close"] = 90
    ra, rb = run(action, data=a, cash=1000), run(action, data=b, cash=1000)
    assert ra._fills.iloc[0].qty == rb._fills.iloc[0].qty == 9


def test_fractional_native_and_sizing_budget():
    spec = InstrumentSpec(quantity_step=0.001, min_notional=1)

    def action(s, i):
        if i == 1:
            assert s.close[-1] == 100
            assert stop_risk(0.01, account=s.account, reference_price=100, stop_price=95).qty == 20
            assert (
                equity_fraction(0.1, account=s.account, reference_price=100, cost_per_unit=1).qty
                == 9
            )
            assert (
                fixed_quantity(0.0039, reference_price=100, instrument=spec).reason
                == "below_min_notional"
            )
            s.buy(qty=0.103)
        if i == 2:
            s.trades[0].close(qty=0.1)
        if i == 3:
            s.trades[0].close()

    r = run(action, instrument=spec, commission=(5, 0))
    assert r._fills.qty.tolist() == [0.103, 0.1, 0.003]
    assert r._trades.Size.sum() == pytest.approx(0.103)
    assert r._trades.Commission.sum() == 15
    assert r._open_trades.empty


def test_target_deduplicate_replace_and_conflict():
    def action(s, i):
        if i == 1:
            s.buy(qty=3)
        if i == 2:
            s.first = s.order_target_quantity(target=10, limit=80)
            assert s.first is s.order_target_quantity(target=10, limit=80)
        if i == 3:
            second = s.order_target_quantity(target=5, limit=80)
            assert s.first.status == OrderStatus.CANCELED and second.request.qty == 2
            second.cancel()
            s.buy(qty=1, limit=80)
            with pytest.raises(ValueError, match="conflicting_pending_order"):
                s.order_target_percent(target=0.1)

    r = run(action)
    assert len(r._orders) == 4
    assert r._orders.iloc[1].reason == "target_replaced"


@pytest.mark.parametrize("mode", ["bars", "absolute"])
def test_expiration_before_matching(mode):
    def action(s, i):
        if i == 1:
            kwargs = (
                {"valid_bars": 1}
                if mode == "bars"
                else {"expires_at": s.data_index[-1] + pd.Timedelta(days=2)}
            )
            s.buy(qty=1, limit=80, **kwargs)

    data = frame()
    data.iloc[3:] = [80, 90, 70, 80]
    r = run(action, data=data)
    assert r._orders.iloc[0].status == "Expired" and r._fills.empty
    assert r._order_events.iloc[-1].bar_index == 3


def test_oco_atomic_pair_and_ambiguity():
    def action(s, i):
        if i == 1:
            with pytest.raises(ValueError):
                s.submit_oco(
                    first=OrderRequest(qty=1, side="buy"), second=OrderRequest(qty=0, side="sell")
                )
            assert not s.orders
            s.group = s.submit_oco(
                first=OrderRequest(qty=1, side="buy", stop=105),
                second=OrderRequest(qty=1, side="sell", stop=95),
            )
        if i == 2:
            assert [o.status for o in s.group.orders] == ["Filled", "Canceled"]
            s.group.cancel()

    r = run(action)
    assert len(r._fills) == 1
    assert r.attrs["diagnostics"][0]["code"] == "ambiguous_oco_bar"


def test_protection_fill_retains_filled_status_and_same_close_delay():
    def action(s, i):
        if i == 1:
            s.buy(qty=1, sl=95, tp=105)

    a = run(action)
    b = run(action, execution_timing="same_close")
    for r in (a, b):
        assert r._trades.ExitPrice.tolist() == [95]
        assert r._orders.query("kind == 'sl'").iloc[0].status == "Filled"
        assert r._orders.query("kind == 'tp'").iloc[0].status == "Canceled"
    assert a._trades.EntryBar.iloc[0] == a._trades.ExitBar.iloc[0] == 2
    assert b._trades.EntryBar.iloc[0] == 1 and b._trades.ExitBar.iloc[0] == 2
    assert any(item["code"] == "ambiguous_bracket_bar" for item in b.attrs["diagnostics"])


def test_empty_tables_metadata_and_values_without_strategy():
    r = Backtest(frame(), Idle).run()
    r = r.drop("_strategy")
    for name in ("_orders", "_fills", "_order_events", "_trade_allocations", "_open_trades"):
        assert r[name].empty and len(r[name].columns) > 0
    assert r._positions.shape[0] == 8
    json.dumps(r.attrs, allow_nan=False)
    restored = pickle.loads(pickle.dumps(r))
    assert restored._final_account == r._final_account


@pytest.mark.parametrize(
    "options,error",
    [
        ({"symbol": ""}, ValueError),
        ({"symbol": 1}, ValueError),
        ({"currency": 1}, TypeError),
        ({"quantity_step": 0}, ValueError),
        ({"quantity_step": True}, TypeError),
        ({"quantity_step": float("nan")}, ValueError),
        ({"min_quantity": 0}, ValueError),
        ({"price_tick": 0}, ValueError),
        ({"min_notional": -1}, ValueError),
    ],
)
def test_invalid_instrument_metadata(options, error):
    with pytest.raises(error):
        InstrumentSpec(**options)


@pytest.mark.parametrize(
    "values",
    [
        {"side": "unknown", "qty": 1},
        {"side": "buy", "qty": 0},
        {"side": "buy", "qty": True},
        {"side": "buy", "qty": -0.1},
        {"side": "buy", "qty": 0.5},
        {"side": "buy", "qty": float("inf")},
        {"side": "buy", "qty": 1, "limit": 0},
        {"side": "buy", "qty": 1, "stop": float("nan")},
        {"side": "buy", "qty": 1, "sl": 101},
        {"side": "sell", "qty": 1, "sl": 99},
        {"side": "buy", "qty": 1, "tp": 99},
        {"side": "sell", "qty": 1, "tp": 101},
        {"side": "buy", "qty": 1, "expires_at": "2026-01-03"},
        {"side": "buy", "qty": 1, "expires_at": pd.NaT},
        {"side": "buy", "qty": 1, "valid_bars": 0},
        {"side": "buy", "qty": 1, "valid_bars": True},
        {"side": "buy", "qty": 1, "valid_bars": 1.5},
        {"side": "buy", "qty": 1, "valid_bars": 1, "expires_at": "2026-01-03T00:00Z"},
        {"side": "buy", "qty": 1, "tag": (1, 2)},
        {"side": "buy", "qty": 1, "tag": {1: "x"}},
        {"side": "buy", "qty": 1, "tag": {"x": [float("nan")]}},
    ],
)
def test_invalid_requests_are_atomic(values):
    def action(s, i):
        if i == 1:
            with pytest.raises((TypeError, ValueError)):
                s._broker.new_order(**values)
            assert not s.orders

    r = run(action)
    assert r._orders.empty and r._fills.empty


@pytest.mark.parametrize(
    "options",
    [
        {"cash": 0},
        {"margin": 0},
        {"margin": 2},
        {"spread": -0.1},
        {"spread": 1},
        {"max_gross_exposure": 0},
        {"commission": (-1, 0)},
        {"commission": 0.1},
        {"execution_timing": "invalid"},
        {"end_policy": "invalid"},
    ],
)
def test_invalid_account_policy(options):
    with pytest.raises(ValueError):
        Backtest(frame(), Idle, **options).run()


@pytest.mark.parametrize(
    "options", [{"mode": "other"}, {"value": 1}, {"mode": "fixed", "value": -1}]
)
def test_invalid_slippage(options):
    with pytest.raises(ValueError):
        Slippage(**options)


def test_tick_grid_data_order_and_execution():
    from openbacktesting.broker.execution import execution_price

    spec = InstrumentSpec(quantity_step=0.1, price_tick=0.05)
    assert spec.price(100.03, side="buy") == 100.05
    assert spec.price(100.03, side="sell") == 100
    with pytest.raises(ValueError):
        spec.price(100.03)
    with pytest.raises(ValueError):
        spec.quantity(0.15)
    bad = frame()
    bad.iloc[0, 0] = 100.03
    with pytest.raises(ValueError):
        Backtest(bad, Idle, instrument=spec)
    for bad in (
        frame().iloc[::-1],
        pd.concat([frame(), frame()]),
        frame().assign(Close=np.inf),
        frame().assign(Open=0),
    ):
        with pytest.raises(ValueError):
            Backtest(bad, Idle)
    kwargs = {"spread": 0, "slippage": Slippage("bps", 10), "instrument": spec, "limit": None}
    assert execution_price(100, "buy", **kwargs) == 100.1
    assert execution_price(100, "sell", **kwargs) == 99.9
    assert execution_price(100, "buy", bounds=(99.01, 99.02), **kwargs) is None
    assert execution_price(100, "buy", **(kwargs | {"limit": 100})) is None
    assert execution_price(100, "sell", **(kwargs | {"limit": 100})) is None


def test_closing_and_protection_validation_and_replacement():
    def action(s, i):
        if i == 1:
            assert s.close_position() == ()
            s.buy(qty=3, sl=80, tp=120)
        if i == 2:
            t = s.trades[0]
            for kwargs in (
                {"portion": 0.5, "qty": 1},
                {"portion": 2},
                {"portion": 0.01},
                {"qty": 0},
            ):
                with pytest.raises(ValueError):
                    t.close(**kwargs)
            for kwargs in ({}, {"amount": 1, "percent": 0.1}, {"percent": 1}):
                with pytest.raises(ValueError):
                    t.set_trailing_stop(**kwargs)
            first = t.set_trailing_stop(amount=10)
            t.sl = 85
            assert first.status == "Canceled" and t._sl_order.trail is None
            t.set_trailing_stop(percent=0.1)
            t.close(qty=1)
        if i == 3:
            assert s.trades[0].size == 2
            assert s.trades[0]._sl_order.trail == ("percent", 0.1)
            s.saved = s.trades[0]
            s.close_position()
        if i == 4:
            with pytest.raises(ValueError):
                s.saved.sl = 90

    r = run(action, data=frame().assign(Low=99, High=101))
    assert r._trades.Size.tolist() == [1, 2]
    assert (r._orders.status.isin(["Filled", "Canceled"])).all()


@pytest.mark.parametrize("direction", ["buy", "sell"])
@pytest.mark.parametrize("mode", ["amount", "percent"])
def test_native_trail_old_stop_first_then_tightens(direction, mode):
    stops = []

    def action(s, i):
        if i == 1:
            getattr(s, direction)(qty=1)
        if i == 2:
            s.trades[0].set_trailing_stop(**{mode: 10 if mode == "amount" else 0.1})
        if i >= 3 and s.trades:
            stops.append(s.trades[0].sl)

    data = frame().assign(Low=99, High=101)
    closes = (
        [100, 100, 100, 105, 102, 106, 104]
        if direction == "buy"
        else [100, 100, 100, 95, 98, 94, 96]
    )
    data["Close"] = closes
    data["High"] = np.maximum(closes, 100) + 1
    data["Low"] = np.minimum(closes, 100) - 1
    r = run(action, data=data)
    assert stops == sorted(stops, reverse=direction == "sell")
    assert len(r._open_trades) == 1


def test_target_zero_expiry_identity_and_short_policy():
    def action(s, i):
        if i == 1:
            assert s.order_target_percent(target=0) is None
            with pytest.raises(ValueError, match="short_not_allowed"):
                s.order_target_quantity(target=-1)
            expiry = s.data_index[-1] + pd.Timedelta(days=4)
            order = s.order_target_percent(target=0.1, limit=80, expires_at=expiry)
            assert order is s.order_target_percent(target=0.1, limit=80, expires_at=expiry)
            assert s.order_target_quantity(target=0) is None
            assert order.status == "Canceled"

    r = run(action, allow_short=False)
    assert len(r._orders) == 1


@pytest.mark.parametrize("termination", ["cancel", "expire", "reject"])
def test_oco_peer_termination(termination):
    def action(s, i):
        if i == 1:
            extra = {"valid_bars": 1} if termination == "expire" else {}
            s.group = s.submit_oco(
                first=OrderRequest(
                    qty=1000 if termination == "reject" else 1,
                    side="buy",
                    limit=100 if termination == "reject" else 80,
                    **extra,
                ),
                second=OrderRequest(qty=1, side="sell", limit=120),
            )
            if termination == "cancel":
                s.group.orders[0].cancel()

    r = run(action)
    assert r._orders.iloc[-1].reason == "oco_peer_terminated"
    assert r._fills.empty


def test_oco_validation_and_initial_expired_member():
    def action(s, i):
        if i == 1:
            for pair in (
                [],
                [{"qty": 1, "side": "buy", "reduce_only": True}, {"qty": 1, "side": "sell"}],
            ):
                with pytest.raises(TypeError):
                    s.submit_oco(pair)
            group = s.submit_oco(
                first=OrderRequest(qty=1, side="buy", expires_at=s.data_index[-1]),
                second=OrderRequest(qty=1, side="sell"),
            )
            assert [o.status for o in group.orders] == ["Expired", "Canceled"]

    assert run(action)._fills.empty


def test_callable_fee_rebates_and_lifecycle_failures():
    calls = []

    def fee(q, p):
        calls.append((q, p))
        return -5

    r = run(
        lambda s, i: s.buy(qty=2) if i == 1 else s.close_position() if i == 2 else None,
        commission=fee,
    )
    assert calls == [(2, 100), (-2, 100)]
    assert r._final_account["balance"] == 10010 and r["Commissions [$]"] == -10
    assert r.attrs["diagnostics"][-1]["code"] == "commission_not_reconstructable"

    class BadStart(Idle):
        def on_start(self):
            raise ValueError("start")

        def on_finish(self, summary):
            assert summary.reason == "error"

    with pytest.raises(ValueError, match="start"):
        Backtest(frame(), BadStart).run()

    class BadFinish(Idle):
        count = 0

        def on_finish(self, summary):
            self.count += 1
            assert self.count == 1
            raise ValueError("finish")

    with pytest.raises(ValueError, match="finish"):
        Backtest(frame(), BadFinish).run()


@pytest.mark.parametrize(
    "function,kwargs",
    [
        (fixed_quantity, {"qty": 1, "cost_per_unit": -1}),
        (equity_fraction, {"fraction": 0.1, "cost_per_unit": -1}),
        (stop_risk, {"fraction": 0.1, "stop_price": 100}),
        (stop_risk, {"fraction": 0.1, "stop_price": 90, "side": "sell"}),
        (stop_risk, {"fraction": 0.1, "stop_price": 90, "side": "bad"}),
        (stop_risk, {"fraction": 0.1, "stop_price": 90, "cost_per_unit": -1}),
    ],
)
def test_sizing_rejects_invalid_budget(function, kwargs):
    def action(s, i):
        if i == 1:
            inputs = {} if function is fixed_quantity else {"account": s.account}
            with pytest.raises(ValueError):
                function(reference_price=100, **inputs, **kwargs)

    run(action)


def test_minimum_opening_and_recompute_without_path():
    from openbacktesting.lib import compute_stats

    def action(s, i):
        if i == 1:
            s.buy(qty=5)
        if i == 2:
            s.sell(qty=6)

    r = run(action, instrument=InstrumentSpec(min_quantity=5))
    assert r._orders.iloc[-1].reason == "min_quantity"
    r = run(
        lambda s, i: s.buy(qty=1) if i == 1 else None, instrument=InstrumentSpec(min_notional=101)
    )
    assert r._orders.iloc[-1].reason == "min_notional"
    legacy = r.drop("_positions")
    assert np.isnan(compute_stats(stats=legacy, data=frame())["Exposure Time [%]"])


def test_zero_equity_target_and_fee_migration_error():
    def action(s, i):
        if i == 1:
            with pytest.raises(TypeError, match=r"Trading state from 0\.1 cannot resume execution"):
                s._broker._commission_func(1, 100)
            original = s._broker.ledger.balance
            s._broker.ledger.balance = 0
            with pytest.raises(ValueError):
                s.order_target_percent(target=0.5)
            with pytest.raises(ValueError):
                equity_fraction(0.5, account=s.account, reference_price=100)
            s._broker.ledger.balance = original

    run(action)


def test_oco_single_trigger_and_bracket_sl_without_tp_hit():
    def action(s, i):
        if i == 1:
            s.submit_oco(
                first=OrderRequest(qty=1, side="buy", stop=105, sl=95, tp=150),
                second=OrderRequest(qty=1, side="sell", stop=80),
            )

    r = run(action)
    assert r._trades.ExitPrice.tolist() == [95]
    assert not any(d["code"].startswith("ambiguous") for d in r.attrs["diagnostics"])


def test_limit_cost_is_not_clipped_into_legal_fill():
    r = run(
        lambda s, i: s.buy(qty=1, limit=100) if i == 1 else None,
        data=frame().assign(High=100),
        slippage=Slippage("fixed", 1),
    )
    assert r._fills.empty


def test_terminal_liquidation_error_propagates_and_finish_observes_error():
    seen = []

    def fee(q, p):
        if q < 0:
            raise ValueError("liquidation fee")
        return 0

    class Hooks(Idle):
        def next(self):
            if len(self.data) == 2:
                self.buy(qty=1)

        def on_finish(self, summary):
            seen.append(summary.reason)

    with pytest.raises(ValueError, match="liquidation fee"):
        Backtest(frame(), Hooks, commission=fee, end_policy="close_at_last_close").run()
    assert seen == ["error"]


def test_public_model_identity_and_entry_fee_nonlinear_allocation():
    from openbacktesting import broker
    from openbacktesting.broker import models

    for name in (
        "OrderSnapshot",
        "OrderEvent",
        "Fill",
        "TradeAllocation",
        "AccountSnapshot",
        "PositionSnapshot",
        "RunSummary",
    ):
        assert getattr(broker, name) is getattr(models, name)
    from openbacktesting.broker.requests import OrderRequest

    assert broker.OrderRequest is OrderRequest
    calls = []

    def fee(q, p):
        calls.append((q, p))
        return q * q

    def action(s, i):
        if i == 1:
            s.buy(qty=10)
        if i in (2, 3):
            s.trades[0].close(qty=5)

    r = run(action, commission=fee)
    assert calls == [(10, 100), (-5, 100), (-5, 100)]
    assert r._trades.Commission.tolist() == [75, 75]
    assert r._final_account["balance"] == 9850


def test_account_mark_and_legal_reduction_under_limits():
    def action(s, i):
        if i == 1:
            s.buy(qty=2)
        if i == 2:
            a = s.account
            p = s.position.snapshot
            assert (a.balance, a.equity, a.margin_used, a.margin_available) == (
                9995,
                10015,
                220,
                9795,
            )
            assert (p.unrealized_pnl_gross, p.unrealized_pnl_net, p.entry_fees_remaining) == (
                20,
                15,
                5,
            )
            assert p.avg_price == 100 and p.return_fraction == 0.075
            s.sell(qty=2)

    data = frame()
    data.iloc[2] = [100, 120, 90, 110]
    data.iloc[3] = [110, 120, 100, 110]
    r = run(action, data=data, commission=(5, 0), allow_short=False, max_gross_exposure=0.021)
    assert r._final_account["balance"] == 10010 and r._open_trades.empty


def test_phase_permissions_and_terminal_order_notifications():
    seen = []

    class Phases(Idle):
        def init(self):
            with pytest.raises(RuntimeError):
                self.buy(qty=1)

        def next(self):
            if len(self.data) == len(frame()):
                self.pending = self.buy(qty=1)

        def on_order(self, event):
            if event.phase == "terminal":
                seen.append(event.snapshot.status)
                with pytest.raises(RuntimeError):
                    self.buy(qty=1)

    r = Backtest(frame(), Phases).run()
    assert seen == ["Canceled"] and r._fills.empty
    assert r._orders.dtypes.equals(
        run(lambda s, i: s.buy(qty=1) if i == 1 else None)._orders.dtypes
    )
    empty = Backtest(frame(), Idle).run()
    for name in ("_orders", "_fills", "_order_events", "_trade_allocations", "_open_trades"):
        assert empty[name].dtypes.equals(r[name].dtypes)


def test_public_bracket_group_cancellation_does_not_flatten():
    def action(s, i):
        if i == 1:
            s.entry = s.buy(qty=2, sl=80, tp=120)
            assert s.entry.group.kind == "bracket"
        if i == 2:
            assert s.trades[0].group is s.entry.group
            assert len(s.entry.group.orders) == 3
            s.trades[0].group.cancel()
            assert s.position.size == 2 and not s.orders
        if i == 3:
            plain = s.buy(qty=1, limit=80)
            assert plain.group is None

    r = run(action)
    assert r._open_trades.Size.tolist() == [2]


def test_resource_probe_smoke():
    import subprocess
    import sys
    from pathlib import Path

    process = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("trading_resource_probe.py")),
            "--bars",
            "1000",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(process.stdout.splitlines()[-1])
    assert result["rows"]["_order_events"] == 6 and result["rows"]["_account_curve"] == 1001


def test_private_account_compatibility_and_zero_reduce_request():
    def action(s, i):
        if i == 1:
            assert s._broker.margin_available == s.account.margin_available
            assert s._broker._cash == s.account.balance
            with pytest.raises(ValueError, match="qty must be a positive finite number"):
                s.sell(qty=0, reduce_only=True)

    run(action)


def test_ohlc_bound_cannot_override_limit():
    from openbacktesting.broker.execution import execution_price

    assert (
        execution_price(
            100,
            "buy",
            spread=0,
            slippage=Slippage(),
            instrument=InstrumentSpec(),
            limit=100,
            bounds=(101, 102),
        )
        is None
    )


def test_target_gap_preserves_request_and_rechecks_cash():
    data = frame()
    data.iloc[2:] = [200, 210, 190, 200]
    r = run(lambda s, i: s.order_target_percent(target=1) if i == 1 else None, data=data, cash=1000)
    assert r._orders.qty.tolist() == [10]
    assert r._orders.iloc[0].reason == "insufficient_funds" and r._fills.empty


def test_native_trailing_updates_during_nan_gate():
    data = frame()
    data.iloc[3] = [100, 121, 99, 120]
    data.iloc[4] = [115, 116, 105, 115]

    class Gated(Idle):
        def init(self):
            self.ind(lambda: np.array([1, 1, 1, np.nan, np.nan, 1, 1]))

        def next(self):
            i = len(self.data) - 1
            if i == 1:
                self.buy(qty=1)
            if i == 2:
                self.trades[0].set_trailing_stop(amount=10)

    r = Backtest(data, Gated).run()
    assert r._trades.ExitBar.tolist() == [4] and r._trades.ExitPrice.tolist() == [110]


def test_parent_expiration_does_not_expire_protection():
    data = frame().assign(High=101, Low=99)
    data.iloc[4] = [100, 101, 89, 90]
    r = run(lambda s, i: s.buy(qty=1, sl=90, valid_bars=1) if i == 1 else None, data=data)
    assert r._trades.ExitBar.tolist() == [4]
    assert r._orders.valid_bars.tolist()[0] == 1
    assert pd.isna(r._orders.valid_bars.tolist()[1])


def test_recompute_full_account_keeps_actual_fees_and_ledger():
    from openbacktesting.lib import compute_stats

    r = run(lambda s, i: s.buy(qty=1) if i == 1 else None, commission=(5, 0))
    again = compute_stats(stats=r, data=frame(), risk_free_rate=0.01)
    assert again["Commissions [$]"] == 5
    assert again["Exposure Time [%]"] == r["Exposure Time [%]"]
    pd.testing.assert_frame_equal(again._fills, r._fills)
    assert again._final_account == r._final_account


def test_numeric_metadata_is_json_safe():
    r = Backtest(
        frame(),
        Idle,
        spread=np.int64(0),
        margin=np.int64(1),
        commission=np.int64(0),
        instrument=InstrumentSpec(price_tick=np.int64(1), min_notional=np.int64(0)),
        slippage=Slippage("fixed", np.int64(0)),
    ).run()
    json.dumps(r.attrs, allow_nan=False)


def test_one_lot_three_exits_preserves_identity_and_fee_remainder():
    def action(s, i):
        if i == 1:
            s.buy(qty=3)
        if i in (2, 3, 4):
            s.trades[0].close(qty=1)

    r = run(action, commission=(5, 0))
    assert r._trades.Size.tolist() == [1, 1, 1]
    assert r._trades.trade_id.nunique() == 1
    assert r["# Trades"] == 3 and r["# Closed Lots"] == 1
    assert r._trades.Commission.sum() == pytest.approx(20)
    assert r._final_account["balance"] == 9980
    assert r._open_trades.empty


def test_same_close_new_limit_waits_until_next_bar():
    r = run(lambda s, i: s.buy(qty=1, limit=100) if i == 1 else None, execution_timing="same_close")
    assert r._fills.bar_index.tolist() == [2]


def test_rejected_bracket_parent_creates_no_children():
    r = run(lambda s, i: s.buy(qty=1000, sl=90, tp=110) if i == 1 else None, cash=1000)
    assert r._orders.status.tolist() == ["Rejected"]
    assert r._orders.reason.tolist() == ["insufficient_funds"]
    assert r._fills.empty


def test_old_ambiguous_order_and_policy_keywords_fail_explicitly():
    def action(s, i):
        if i == 1:
            with pytest.raises(TypeError, match="qty"):
                s.buy()
            with pytest.raises(TypeError, match="size"):
                s.buy(size=0.1)

    run(action)
    for keyword in ("trade_on_close", "finalize_trades"):
        with pytest.raises(TypeError, match=keyword):
            Backtest(frame(), Idle, **{keyword: True})


def test_typed_result_columns_preserve_nested_tags_and_empty_schema():
    data = frame()
    tag = ["alpha", {"levels": [1, 2]}]
    populated = run(lambda s, i: s.buy(qty=1, tag=tag) if i == 1 else None, data=data)
    empty = Backtest(data, Idle).run()
    assert populated._open_trades.Tag.iloc[0] == tag
    assert populated._open_trades.EntryTime.dtype == object
    assert populated._fills.timestamp.dtype == object
    assert populated._fills.timestamp.iloc[0] == data.index[2]
    for key in (
        "_orders",
        "_order_events",
        "_fills",
        "_trade_allocations",
        "_positions",
        "_account_curve",
        "_open_trades",
    ):
        assert populated[key].dtypes.equals(empty[key].dtypes), key


@pytest.mark.parametrize(
    "side,stop,ohlc,expected",
    [
        ("buy", 100, [110, 115, 105, 110], 111),
        ("sell", 100, [90, 95, 85, 90], 89),
    ],
)
def test_stop_gap_uses_open_before_execution_cost(side, stop, ohlc, expected):
    data = frame()
    data.iloc[2] = ohlc
    r = run(
        lambda s, i: getattr(s, side)(qty=1, stop=stop) if i == 1 else None,
        data=data,
        slippage=Slippage("fixed", 1),
    )
    assert r._fills.bar_index.tolist() == [2]
    assert r._fills.price.tolist() == [expected]
