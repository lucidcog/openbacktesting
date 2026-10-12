"""Strategy settings: plain-value round-trips, request budgets, real fees, and statistical baselines."""

import json
import pickle
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from openbacktesting import (
    Backtest,
    CommissionType,
    DataContext,
    DefaultOrderSize,
    EndPolicy,
    ExecutionTiming,
    QuantityType,
    Strategy,
    Timeframe,
    backtest,
    inputs,
    runtime,
)
from openbacktesting.broker import Commission, InstrumentSpec, OrderRequest
from openbacktesting.broker.commission import normalize_commission
from openbacktesting.lib import compute_stats
from openbacktesting.simulation.config import BacktestSettings
from openbacktesting.test import GOOG


def frame():
    return pd.DataFrame(
        {"Open": 100.0, "High": 110.0, "Low": 90.0, "Close": 100.0},
        index=pd.date_range("2026-01-01", periods=8, tz="UTC"),
    )


class Idle(Strategy):
    def init(self):
        pass

    def next(self):
        pass


def run(action, **settings):
    class Script(Idle):
        def next(self):
            action(self, len(self.data) - 1)

    return Backtest(settings.pop("data", frame()), Script, **settings).run()


def run_flat(action, **settings):
    """Run identical behavior through author declarations/host entry points with assertions shared by the low-level entry point."""
    data = settings.pop("data", frame())
    instrument = settings.pop("instrument", InstrumentSpec())
    size = settings.pop("default_order_size", None)
    model = settings.pop("commission", Commission())
    assert sum(value != 0 for value in (model.fixed, model.relative, model.per_unit)) <= 1
    settings.update(
        default_qty_type=QuantityType.PERCENT_OF_EQUITY
        if size is not None and size.mode == "equity_fraction"
        else QuantityType.FIXED,
        default_qty_value=None
        if size is None
        else size.value * (100 if size.mode == "equity_fraction" else 1),
        commission_type=CommissionType.CASH_PER_ORDER
        if model.fixed
        else CommissionType.CASH_PER_CONTRACT
        if model.per_unit
        else CommissionType.PERCENT,
        commission_value=model.fixed or model.per_unit or model.relative * 100,
        end_policy=EndPolicy(settings.pop("end_policy", "mark_to_market")),
        execution_timing=ExecutionTiming(settings.pop("execution_timing", "next_open")),
    )

    @backtest(**settings)
    class Script(Idle):
        def next(self):
            action(self, len(self.data) - 1)

    return runtime.run(
        {"__name__": __name__, "script": Script},
        data=data,
        context=DataContext(Timeframe.days(1), "UTC"),
        instrument=instrument,
    )


@pytest.mark.parametrize(
    "value",
    [
        DefaultOrderSize("fixed", 2.5),
        DefaultOrderSize("equity_fraction", 0.3),
        Commission(1, -0.001, 0.5),
    ],
)
def test_values_roundtrip_and_freezing(value):
    assert pickle.loads(pickle.dumps(value)) == value
    snapshot = value.snapshot()
    assert type(value).from_snapshot(json.loads(json.dumps(snapshot))) == value
    snapshot[next(iter(snapshot))] = "changed"
    assert snapshot != value.snapshot()
    with pytest.raises(FrozenInstanceError):
        value.value = 10


@pytest.mark.parametrize(
    "mode,value",
    [
        ("cash", 1),
        (None, 1),
        ([], 1),
        ("fixed", 0),
        ("fixed", -1),
        ("fixed", True),
        ("fixed", "1"),
        ("fixed", None),
        ("fixed", np.nan),
        ("fixed", np.inf),
        ("equity_fraction", 1.01),
    ],
)
def test_invalid_default_size(mode, value):
    with pytest.raises((TypeError, ValueError)):
        DefaultOrderSize(mode, value)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fixed": -1},
        {"per_unit": -1},
        {"relative": -0.101},
        {"relative": 0.1},
        {"fixed": True},
        {"per_unit": np.inf},
        {"relative": np.nan},
        {"fixed": None},
    ],
)
def test_invalid_commission(kwargs):
    with pytest.raises((TypeError, ValueError)):
        Commission(**kwargs)


@pytest.mark.parametrize("model", [Commission(), DefaultOrderSize("fixed", 1)])
def test_strict_snapshot_fields(model):
    for invalid in (None, [], 1):
        with pytest.raises(TypeError):
            type(model).from_snapshot(invalid)
    for invalid in ({}, model.snapshot() | {"extra": 1}):
        with pytest.raises(ValueError):
            type(model).from_snapshot(invalid)


@pytest.mark.parametrize(
    "patch", [{"version": 2}, {"version": True}, {"version": 1.0}, {"kind": "other"}]
)
def test_commission_snapshot_version(patch):
    with pytest.raises(ValueError):
        Commission.from_snapshot(Commission().snapshot() | patch)


def test_normalize_commission_and_legacy_shapes():
    assert normalize_commission(0.002) == Commission(relative=0.002)
    assert normalize_commission((2, 0.002)) == Commission(2, 0.002)
    assert Backtest(frame(), Idle, commission=0.002).run().attrs["commission"] == (0, 0.002)
    assert Backtest(frame(), Idle, commission=(2, 0.002)).run().attrs["commission"] == (2, 0.002)
    with pytest.raises(ValueError):
        normalize_commission((1,))
    with pytest.raises(TypeError):
        normalize_commission(lambda q, p: 0)


@pytest.mark.parametrize("bad", [True, None, "0.02", np.nan, np.inf, -1, 1])
def test_invalid_rate_at_public_boundaries(bad):
    for make in (
        lambda: backtest(risk_free_rate=bad),
        lambda: Backtest(frame(), Idle, risk_free_rate=bad),
    ):
        with pytest.raises((ValueError, TypeError)):
            make()
    result = Backtest(frame(), Idle).run()
    with pytest.raises((ValueError, TypeError)):
        compute_stats(stats=result, data=frame(), risk_free_rate=bad)


def test_invalid_size_and_commission_before_lifecycle():
    for bad in ({}, False, 1):
        with pytest.raises(TypeError):
            Backtest(frame(), Idle, default_order_size=bad)
        with pytest.raises(TypeError):
            backtest(default_order_size=bad)
    for bad in (None, {}, (1,)):
        with pytest.raises((TypeError, ValueError)):
            Backtest(frame(), Idle, commission=bad)


@backtest(
    risk_free_rate=0.02,
    default_qty_type=QuantityType.FIXED,
    default_qty_value=2.5,
    commission_type=CommissionType.CASH_PER_CONTRACT,
    commission_value=1.5,
)
class Declared(Idle):
    length = inputs.int(4, title="Exit position", minval=3)

    def next(self):
        if len(self.data) == 2:
            self.buy()
        elif len(self.data) == self.length:
            self.close_position()


def context(data=None, step=1):
    return {
        "data": frame() if data is None else data,
        "context": DataContext(Timeframe.days(1), "UTC"),
        "instrument": InstrumentSpec(quantity_step=step),
    }


def test_runtime_settings_cover_snapshot_and_isolation():
    namespace = {"__name__": __name__, "Script": Declared}
    described = runtime.describe(namespace)
    settings = described["backtest"]["settings"]
    assert settings["commission_type"] == "cash_per_contract"
    assert settings["commission_value"] == 1.5
    assert settings["default_qty_type"] == "fixed"
    assert settings["default_qty_value"] == 2.5
    settings["default_qty_value"] = 100
    settings["commission_value"] = 100
    first = runtime.run(namespace, **context())
    second = runtime.run(namespace, **context(step=0.1), settings={"risk_free_rate": 0})
    assert first._fills.qty.tolist() == [2, 2]
    assert first._fills.fee.tolist() == [3, 3]
    assert second._fills.qty.tolist() == [2.5, 2.5]
    assert second.attrs["statistics_risk_free_rate"] == 0
    assert first.attrs["statistics_risk_free_rate"] == 0.02
    assert runtime.describe(namespace)["schemaHash"] == described["schemaHash"]
    assert runtime.describe(namespace)["backtest"]["settings"]["risk_free_rate"] == 0.02
    with pytest.raises(TypeError, match="qty"):
        runtime.run(namespace, **context(), settings={"default_qty_value": None})
    with pytest.raises(TypeError, match="qty"):
        Backtest(frame(), Declared).run()
    direct = Backtest(
        frame(),
        Declared,
        context=context()["context"],
        commission=Commission(per_unit=1.5),
        risk_free_rate=0.02,
        default_order_size=DefaultOrderSize("fixed", 2.5),
    ).run()
    pd.testing.assert_frame_equal(first._fills, direct._fills)
    assert direct.attrs["commission"] == Commission(per_unit=1.5).snapshot()
    assert "commission_not_reconstructable" not in [d["code"] for d in direct.attrs["diagnostics"]]


class Long(Idle):
    def next(self):
        if len(self.data) == 2:
            self.buy(qty=10)
        elif len(self.data) == 55:
            self.close_position()


def test_rate_formulas_recompute_and_original_facts():
    data = GOOG.iloc[:80]
    zero = Backtest(data, Long).run()
    nonzero = Backtest(data, Long, risk_free_rate=0.02).run()
    for name in ("_fills", "_trades", "_orders", "_account_curve", "_equity_curve"):
        pd.testing.assert_frame_equal(zero[name], nonzero[name])
    assert nonzero["Sharpe Ratio"] == pytest.approx(
        zero["Sharpe Ratio"] - 2 / zero["Volatility (Ann.) [%]"]
    )
    days = nonzero._equity_curve.Equity.pct_change()
    days.iloc[0] = (
        nonzero._equity_curve.Equity.iloc[0] / nonzero.attrs["statistics_initial_equity"] - 1
    )
    downside = np.sqrt((days.clip(upper=0) ** 2).mean()) * np.sqrt(252)
    assert nonzero["Sortino Ratio"] == pytest.approx(zero["Sortino Ratio"] - 0.02 / downside)
    assert nonzero["Alpha [%]"] == pytest.approx(zero["Alpha [%]"] + 2 * (zero["Beta"] - 1))
    nonzero.attrs["backtest_snapshot"] = {"settings": {"risk_free_rate": 0.02}}
    inherited = compute_stats(stats=nonzero, data=data)
    overridden = compute_stats(stats=inherited, data=data, risk_free_rate=0.0)
    repeated = compute_stats(stats=overridden, data=data)
    subset = compute_stats(stats=nonzero, data=data, trades=nonzero._trades.iloc[:1])
    assert [
        r.attrs["statistics_risk_free_rate"] for r in (inherited, overridden, repeated, subset)
    ] == [0.02, 0, 0, 0.02]
    for result in (inherited, overridden, repeated):
        pd.testing.assert_frame_equal(result._fills, nonzero._fills)
        assert result.attrs["backtest_snapshot"]["settings"]["risk_free_rate"] == 0.02
    assert nonzero.attrs["statistics_risk_free_rate"] == 0.02
    old = zero.copy()
    del old.attrs["statistics_risk_free_rate"]
    assert compute_stats(stats=old, data=data).attrs["statistics_risk_free_rate"] == 0
    old.attrs["statistics_risk_free_rate"] = None
    with pytest.raises(TypeError):
        compute_stats(stats=old, data=data)
    assert (
        compute_stats(stats=old, data=data, risk_free_rate=0.01).attrs["statistics_risk_free_rate"]
        == 0.01
    )


@pytest.mark.parametrize("method", ["buy", "sell"])
@pytest.mark.parametrize("entry", [run, run_flat])
def test_default_fixed_and_explicit_priority(method, entry):
    def action(s, i):
        if i == 1:
            getattr(s, method)()
            getattr(s, method)(qty=0.5)
            for bad in (None, 0, 0.55, True):
                with pytest.raises((ValueError, TypeError)):
                    getattr(s, method)(qty=bad)

    result = entry(
        action,
        default_order_size=DefaultOrderSize("fixed", 1.29),
        instrument=InstrumentSpec(quantity_step=0.1),
    )
    assert result._fills.qty.tolist() == [1.2, 0.5]


@pytest.mark.parametrize("margin", [1, 0.2])
@pytest.mark.parametrize("entry", [run, run_flat])
def test_equity_default_frozen_and_no_pending_reservation(margin, entry):
    def action(s, i):
        if i == 1:
            s.buy(limit=99)
            s.buy(stop=105)

    result = entry(
        action, margin=margin, default_order_size=DefaultOrderSize("equity_fraction", 0.1)
    )
    assert result._orders.qty.tolist() == [10, 10]
    assert result._fills.qty.tolist() == [10, 10]
    assert result._fills.price.tolist() == [99, 105]


@pytest.mark.parametrize(
    "instrument,reason",
    [
        (InstrumentSpec(min_quantity=2), "below_min_quantity"),
        (InstrumentSpec(min_notional=150), "below_min_notional"),
    ],
)
@pytest.mark.parametrize("entry", [run, run_flat])
def test_budget_error_has_no_side_effects(instrument, reason, entry):
    def action(s, i):
        if i == 1:
            old = s.buy(qty=2, limit=80)
            events = len(s._broker.events)
            with pytest.raises(ValueError, match=reason):
                s.buy()
            assert s.orders == (old,)
            assert len(s._broker.events) == events

    result = entry(
        action,
        instrument=instrument,
        exclusive_orders=True,
        default_order_size=DefaultOrderSize("fixed", 1),
    )
    assert len(result._orders) == 1 and result._fills.empty


def test_quantity_permissions_and_reduce_only():
    class Phases(Idle):
        def init(self):
            with pytest.raises(RuntimeError, match="lifecycle"):
                self.buy()

        def on_start(self):
            with pytest.raises(RuntimeError):
                self.sell()

        def next(self):
            if len(self.data) == 2:
                with pytest.raises(TypeError, match="qty"):
                    self.sell(reduce_only=True)
                self.buy()

        def on_fill(self, fill):
            if fill.side == "buy":
                self.sell()

        def on_finish(self, summary):
            with pytest.raises(RuntimeError):
                self.buy()

    result = Backtest(
        frame(),
        Phases,
        default_order_size=DefaultOrderSize("fixed", 2),
        execution_timing="same_close",
    ).run()
    assert result._fills.bar_index.tolist() == [1, 2]
    assert result._fills.qty.tolist() == [2, 2]


@pytest.mark.parametrize("gap,fee", [(200, 0), (100, 1)])
@pytest.mark.parametrize("entry", [run, run_flat])
def test_frozen_full_equity_can_be_rejected(gap, fee, entry):
    data = frame()
    data.iloc[2:, :4] = [gap, gap + 10, gap - 10, gap]
    result = entry(
        lambda s, i: s.buy() if i == 1 else None,
        data=data,
        default_order_size=DefaultOrderSize("equity_fraction", 1),
        commission=Commission(per_unit=fee),
    )
    assert result._orders.qty.tolist() == [100]
    assert result._orders.status.tolist() == ["Rejected"]
    assert result._fills.empty


@pytest.mark.parametrize("commission", [0.002, (0, 0.002), Commission(relative=0.002)])
def test_old_fee_inputs_equivalent(commission):
    result = run(
        lambda s, i: s.buy(qty=2) if i == 1 else s.close_position() if i == 3 else None,
        commission=commission,
    )
    assert result._fills.fee.tolist() == [0.4, 0.4]
    assert result._final_account["fees_paid"] == 0.8
    if not isinstance(commission, Commission):
        assert result.attrs["commission"] == (0, 0.002)


@pytest.mark.parametrize("end", ["mark_to_market", "close_at_last_close"])
@pytest.mark.parametrize(
    "model",
    [
        Commission(5, 0.001, 1.5),
        Commission(fixed=5),
        Commission(relative=0.002),
        Commission(per_unit=0.5),
    ],
)
def test_model_fee_allocations_and_reconstruction(end, model):
    def action(s, i):
        if i == 1:
            s.buy(qty=2)
            s.buy(qty=3)
        elif i == 2:
            s.sell(qty=7)
        elif i == 3:
            s.trades[0].close(0.5)

    entry = run if model == Commission(5, 0.001, 1.5) else run_flat
    result = entry(action, commission=model, end_policy=end)
    for fill in result._fills.itertuples():
        assert fill.fee == pytest.approx(
            model.fixed + fill.qty * (fill.price * model.relative + model.per_unit)
        )
        assert result._trade_allocations.query(
            "fill_id == @fill.fill_id"
        ).fee.sum() == pytest.approx(fill.fee)
    assert result._final_account["fees_paid"] == pytest.approx(result._fills.fee.sum())
    assert (
        result._trades.Commission.sum() + result._open_trades.EntryFeeRemaining.sum()
        == pytest.approx(result._fills.fee.sum())
    )
    restored = run(
        action,
        commission=Commission.from_snapshot(json.loads(json.dumps(result.attrs["commission"]))),
        end_policy=end,
    )
    pd.testing.assert_frame_equal(result._fills, restored._fills)
    pd.testing.assert_frame_equal(compute_stats(stats=result, data=frame())._fills, result._fills)


@pytest.mark.parametrize("hedging", [False, True])
@pytest.mark.parametrize("entry", [run, run_flat])
def test_default_reverse_target_and_explicit_exit(hedging, entry):
    def action(s, i):
        if i == 1:
            s.buy()
        elif i == 2:
            s.sell()
        elif i == 3:
            if hedging:
                assert len(s.trades) == 2 and s.position.size == 0
            else:
                assert not s.trades
                s.order_target_quantity(target=3)
        elif i == 4:
            s.close_position()

    result = entry(action, default_order_size=DefaultOrderSize("fixed", 2), hedging=hedging)
    assert result._fills.qty.tolist() == ([2, 2, 2, 2] if hedging else [2, 2, 3, 3])
    assert result._open_trades.empty


@pytest.mark.parametrize("entry", [run, run_flat])
def test_defaults_do_not_supply_oco_or_protection_quantities(entry):
    def action(s, i):
        if i == 1:
            s.submit_oco(
                first=OrderRequest(side="buy", qty=3, limit=95, tp=105),
                second=OrderRequest(side="sell", qty=3, stop=80),
            )

    result = entry(
        action,
        default_order_size=DefaultOrderSize("fixed", 10),
        commission=Commission(per_unit=0.5),
    )
    assert result._fills.qty.tolist() == [3, 3]
    assert result._fills.fee.tolist() == [1.5, 1.5]
    assert result._open_trades.empty


@pytest.mark.parametrize("side,stop", [("buy", 95), ("sell", 105)])
@pytest.mark.parametrize(
    "model,fee",
    [
        (Commission(1, 0, 2), 2),
        (Commission(fixed=1), 1),
        (Commission(relative=0.002), None),
        (Commission(per_unit=2), 1),
    ],
)
def test_fractional_protection_fee(side, stop, model, fee):
    entry = run if model == Commission(1, 0, 2) else run_flat
    result = entry(
        lambda s, i: getattr(s, side)(sl=stop) if i == 1 else None,
        instrument=InstrumentSpec(quantity_step=0.1),
        default_order_size=DefaultOrderSize("fixed", 0.5),
        commission=model,
    )
    assert result._fills.qty.tolist() == [0.5, 0.5]
    expected = [fee, fee] if fee is not None else [p * 0.5 * 0.002 for p in result._fills.price]
    assert result._fills.fee.tolist() == expected
    assert result._trades.Commission.sum() == pytest.approx(sum(expected))


def test_per_unit_insolvency_liquidation_preserves_deficit():
    data = frame()
    data.iloc[3:, :4] = [1, 2, 0.5, 1]
    result = run(
        lambda s, i: s.buy(qty=15) if i == 1 else None,
        data=data,
        cash=1000,
        margin=0.5,
        commission=Commission(per_unit=1),
    )
    assert result._fills.qty.tolist() == [15, 15]
    assert result._fills.fee.tolist() == [15, 15]
    assert result._final_account["balance"] == -515
    assert result._open_trades.empty


def test_flat_overrides_change_type_with_explicit_value():
    ns = {"__name__": __name__, "script": Declared}
    result = runtime.run(
        ns,
        **context(),
        settings={
            "commission_type": CommissionType.CASH_PER_ORDER,
            "commission_value": 5,
            "default_qty_value": 1,
        },
    )
    assert result._fills.qty.tolist() == [1, 1]
    assert result._fills.fee.tolist() == [5, 5]
    assert runtime.describe(ns)["backtest"]["settings"]["commission_value"] == 1.5


@pytest.mark.parametrize("kind", list(CommissionType))
def test_flat_fee_causes_full_equity_rejection(kind):
    settings = BacktestSettings(
        commission_type=kind,
        commission_value=1,
        default_qty_type=QuantityType.PERCENT_OF_EQUITY,
        default_qty_value=100,
    )
    result = run(lambda s, i: s.buy() if i == 1 else None, **settings.kwargs())
    assert result._orders.qty.tolist() == [100]
    assert result._orders.status.tolist() == ["Rejected"]
    assert result._fills.empty and result._final_account["fees_paid"] == 0
