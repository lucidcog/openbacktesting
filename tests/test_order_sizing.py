"""Observable sizing intent and submission snapshots for ordinary and OCO orders across three modes."""

import multiprocessing as mp
import pickle
from dataclasses import FrozenInstanceError, replace

import pandas as pd
import pytest
from test_order_api import state
from test_strategy_settings import run_flat
from test_trading_core import Idle, frame, run

from openbacktesting import Backtest, DefaultOrderSize
from openbacktesting.broker import (
    AccountSnapshot,
    Commission,
    InstrumentSpec,
    OrderRequest,
    OrderSizingSnapshot,
)
from openbacktesting.broker.sizing import _SizeIntent, resolve_size, select_size


def account(equity=10_000):
    return AccountSnapshot(equity, equity, 0, 0, 0, 0, equity, 0, 0)


@pytest.mark.parametrize("mode", ["qty", "amount", "percent"])
@pytest.mark.parametrize("value", [None, True, False, "1", 0, -1, float("nan"), float("inf")])
def test_size_invalid_values(mode, value):
    with pytest.raises((TypeError, ValueError)):
        select_size(**{mode: value})


def test_size_selection_conflicts_defaults_and_reduce_only():
    for values in ({"qty": 1, "amount": None}, {"amount": 2, "percent": 20}):
        with pytest.raises(TypeError, match="mutually exclusive"):
            select_size(**values)
    with pytest.raises(TypeError, match="qty"):
        select_size()
    with pytest.raises(ValueError, match="percent"):
        select_size(percent=100.1)
    with pytest.raises(TypeError, match="bool"):
        select_size(qty=2, reduce_only=1)
    for values in ({}, {"amount": 10}, {"percent": 20}):
        with pytest.raises(TypeError, match="Reduce-only"):
            select_size(**values, reduce_only=True)
    default = _SizeIntent("percent", 20, "default")
    assert select_size(default=default) is default
    assert select_size(qty=2, default=default, reduce_only=True) == _SizeIntent("qty", 2)
    assert select_size(percent=100).value == 100


@pytest.mark.parametrize(
    "intent,expected,budget",
    [
        (select_size(qty=0.2), 0.2, None),
        (select_size(amount=13), 0.1, 13),
        (select_size(percent=20), 20, 2000),
        (_SizeIntent("qty", 1.29, "default"), 1.25, None),
    ],
)
def test_size_resolution_and_frozen_snapshot(intent, expected, budget):
    result = resolve_size(
        intent,
        account=account(),
        reference_price=100,
        instrument=InstrumentSpec(quantity_step=0.05),
    )
    assert result == OrderSizingSnapshot(
        intent.mode, intent.source, intent.value, 10000, 100, budget, expected
    )
    assert pickle.loads(pickle.dumps(result)) == result
    with pytest.raises(FrozenInstanceError):
        result.qty = 999


@pytest.mark.parametrize(
    "intent,instrument,reason",
    [
        (select_size(qty=0.13), InstrumentSpec(quantity_step=0.05), "grid"),
        (select_size(amount=1), InstrumentSpec(), "below_min_quantity"),
        (select_size(percent=1), InstrumentSpec(min_quantity=2), "below_min_quantity"),
        (select_size(amount=100), InstrumentSpec(min_notional=101), "below_min_notional"),
        (_SizeIntent("qty", 1, "default"), InstrumentSpec(min_notional=101), "below_min_notional"),
    ],
)
def test_size_resolution_rejects_invalid_quantity(intent, instrument, reason):
    with pytest.raises(ValueError, match=reason):
        resolve_size(intent, account=account(), reference_price=100, instrument=instrument)


def test_equity_requirement_and_nonfinite_intermediate():
    for equity in (0, -100):
        with pytest.raises(ValueError, match="equity"):
            resolve_size(
                select_size(percent=20),
                account=account(equity),
                reference_price=100,
                instrument=InstrumentSpec(),
            )
        for intent in (select_size(qty=1), select_size(amount=100)):
            assert (
                resolve_size(
                    intent,
                    account=account(equity),
                    reference_price=100,
                    instrument=InstrumentSpec(),
                ).qty
                == 1
            )
    with pytest.raises(ValueError, match="Budgeted quantity"):
        resolve_size(
            select_size(amount=1e308),
            account=account(),
            reference_price=1e-308,
            instrument=InstrumentSpec(),
        )
    with pytest.raises(ValueError, match="Budgeted notional amount"):
        resolve_size(
            _SizeIntent("qty", 1e308, "default"),
            account=account(),
            reference_price=100,
            instrument=InstrumentSpec(),
        )
    result = resolve_size(
        select_size(qty=0.1, reduce_only=True),
        account=account(),
        reference_price=100,
        instrument=InstrumentSpec(quantity_step=0.1, min_quantity=1),
        reduce_only=True,
    )
    assert result.qty == 0.1
    # Existing margin does not change the equity denominator.
    tied = replace(account(), margin_used=9000, margin_available=1000)
    assert (
        resolve_size(
            select_size(percent=20), account=tied, reference_price=100, instrument=InstrumentSpec()
        ).qty
        == 20
    )


@pytest.mark.parametrize("entry", [run, run_flat])
@pytest.mark.parametrize("method", ["buy", "sell"])
@pytest.mark.parametrize("margin", [1, 0.2])
def test_order_modes_share_defaults_and_snapshot(entry, method, margin):
    def action(s, i):
        if i == 0:
            for kwargs in ({}, {"percent": 20}, {"amount": 13}, {"qty": 0.2}):
                order = getattr(s, method)(**kwargs)
                assert order.sizing.qty == order.request.qty
                with pytest.raises(AttributeError):
                    order.sizing = None

    result = entry(
        action,
        instrument=InstrumentSpec(quantity_step=0.05),
        margin=margin,
        default_order_size=DefaultOrderSize("fixed", 1.29),
    )
    assert result._fills.qty.tolist() == [1.25, 20, 0.1, 0.2]
    sizes = result._order_sizing
    assert sizes["mode"].tolist() == ["qty", "percent", "amount", "qty"]
    assert sizes.source.tolist() == ["default", "explicit", "explicit", "explicit"]
    assert sizes.value.tolist() == [1.29, 20, 13, 0.2]
    assert sizes.equity.tolist() == [10000] * 4
    assert sizes.budget.iloc[1:3].tolist() == [2000, 13]
    assert sizes.budget.iloc[[0, 3]].isna().all()


@pytest.mark.parametrize("method", ["buy", "sell"])
def test_invalid_order_size_has_no_side_effects(method):
    def action(s, i):
        if i == 0:
            s.buy(qty=1, limit=80)
            before = state(s)
            for args in (
                {"qty": 1, "amount": None},
                {"amount": 1, "percent": 20},
                {"percent": None},
                {"amount": True},
                {"amount": 1},
                {"percent": 101},
                {"percent": 0.0001},
                {"percent": 20, "reduce_only": True},
                {"amount": 2000, "reduce_only": True},
                {"amount": 2000, "reduce_only": 1},
                {"reduce_only": True},
                {"amount": 100, "limit": -1},
            ):
                with pytest.raises((TypeError, ValueError)):
                    getattr(s, method)(**args)
                assert state(s) == before

    result = run(
        action, exclusive_orders=True, default_order_size=DefaultOrderSize("equity_fraction", 0.2)
    )
    assert result._order_sizing.order_id.tolist() == ["order-1"]


@pytest.mark.parametrize(
    "conditions", [{}, {"limit": 95}, {"stop": 105}, {"stop": 105, "limit": 103}]
)
@pytest.mark.parametrize("timing", ["next_open", "same_close"])
def test_price_conditions_do_not_change_budget_reference(conditions, timing):
    result = run(
        lambda s, i: s.buy(amount=2000, **conditions) if i == 0 else None, execution_timing=timing
    )
    assert result._orders.qty.tolist() == [20]
    assert result._fills.qty.tolist() == [20]
    assert result._order_sizing.reference_price.tolist() == [100]
    assert result._order_sizing.budget.tolist() == [2000]
    expected_bar = 0 if timing == "same_close" and not conditions else 1
    if "stop" in conditions and "limit" in conditions:
        # OHLC cannot prove a return to the limit after triggering; existing matching defers until the next bar.
        expected_bar = 2
    assert result._fills.bar_index.tolist() == [expected_bar]


@pytest.mark.parametrize("gap,fee", [(200, 0), (100, 1)])
def test_rejected_budget_keeps_original_sizing(gap, fee):
    data = frame()
    data.iloc[1:, :4] = [gap, gap + 10, gap - 10, gap]
    result = run(
        lambda s, i: s.buy(percent=100) if i == 0 else None,
        data=data,
        commission=Commission(per_unit=fee),
    )
    assert result._orders.status.tolist() == ["Rejected"]
    assert result._fills.empty
    assert result._order_sizing.qty.tolist() == [100]
    assert result._order_sizing.budget.tolist() == [10000]


@pytest.mark.parametrize("gap,fee", [(200, 0), (100, 1)])
def test_oco_budget_rejection_cancels_sibling_without_resizing(gap, fee):
    data = frame()
    data.iloc[1:, :4] = [gap, gap + 10, gap - 10, gap]

    def action(s, i):
        if i == 0:
            s.submit_oco(
                first=OrderRequest(side="buy", percent=100),
                second=OrderRequest(side="sell", amount=1000, stop=50),
            )

    result = run(action, data=data, commission=Commission(per_unit=fee))
    assert result._orders.status.tolist() == ["Rejected", "Canceled"]
    assert result._fills.empty
    assert result._order_sizing.qty.tolist() == [100, 10]
    assert result._order_sizing.reference_price.tolist() == [100, 100]


@pytest.mark.parametrize("entry", [run, run_flat])
def test_default_percent_preserves_public_scale_and_explicit_override(entry):
    def action(s, i):
        if i == 0:
            s.buy()
            s.buy(amount=100)

    result = entry(action, default_order_size=DefaultOrderSize("equity_fraction", 0.2))
    sizes = result._order_sizing
    assert sizes["mode"].tolist() == ["percent", "amount"]
    assert sizes.source.tolist() == ["default", "explicit"]
    assert sizes.value.tolist() == [20, 100]
    assert sizes.qty.tolist() == [20, 1]


def test_new_modes_respect_lifecycle_and_reverse_increment():
    class Script(Idle):
        def init(self):
            with pytest.raises(RuntimeError):
                self.buy(amount=100)

        def on_start(self):
            with pytest.raises(RuntimeError):
                self.sell(percent=20)

        def next(self):
            if self.bar_index == 0:
                self.buy(qty=15)
            if self.bar_index == 1:
                self.sell(percent=5)

        def on_finish(self, summary):
            with pytest.raises(RuntimeError):
                self.sell(amount=100)

    result = Backtest(frame(), Script).run()
    assert result._fills.qty.tolist() == [15, 5]
    assert result._open_trades.Size.tolist() == [10]


@pytest.mark.parametrize("mode,value", [("qty", 2), ("amount", 2000), ("percent", 20)])
def test_request_intent_is_detached_and_immutable(mode, value):
    tag = {"purpose": ["original"]}
    request = OrderRequest(side="buy", **{mode: value}, tag=tag)
    assert [getattr(request, name) for name in ("qty", "amount", "percent")] == [
        value if name == mode else None for name in ("qty", "amount", "percent")
    ]
    tag["purpose"].append("changed")
    request.tag["purpose"].append("changed")
    assert request.tag == {"purpose": ["original"]}
    assert pickle.loads(pickle.dumps(request)) == request
    with pytest.raises(FrozenInstanceError):
        request._size = select_size(qty=99)
    for args in ({}, {mode: None}, {"qty": 1, "amount": 2}, {"percent": 101}):
        with pytest.raises((TypeError, ValueError)):
            OrderRequest(side="buy", **args)


@pytest.mark.parametrize("cash,price,expected", [(10000, 200, [10, 10]), (20000, 100, [40, 20])])
def test_oco_uses_submission_context_and_preserves_requests(cash, price, expected):
    first = OrderRequest(side="buy", percent=20, limit=1)
    second = OrderRequest(side="buy", amount=2000, limit=2)

    class Script(Idle):
        def init(self):
            self.requests = first, second
            with pytest.raises(RuntimeError):
                self.submit_oco(first=first, second=second)

        def next(self):
            if self.bar_index == 1:
                self.submit_oco(first=first, second=second)

    data = frame()
    data.iloc[1:, :4] = [price, price + 10, price - 10, price]
    result = Backtest(
        data, Script, cash=cash, default_order_size=DefaultOrderSize("fixed", 1)
    ).run()
    assert result._orders.qty.tolist() == expected
    assert result._order_sizing.equity.tolist() == [cash, cash]
    assert result._order_sizing.reference_price.tolist() == [price, price]
    assert result._order_sizing.source.tolist() == ["explicit", "explicit"]
    assert first.percent == 20 and first.qty is None
    assert second.amount == 2000 and second.qty is None


@pytest.mark.parametrize(
    "second",
    [
        OrderRequest(side="sell", amount=1, stop=95),
        OrderRequest(side="sell", percent=0.0001, stop=95),
        OrderRequest(side="sell", percent=20, sl=90),
        OrderRequest(side="buy", amount=2000, limit=100.5),
    ],
)
def test_oco_sizing_or_condition_failure_is_atomic(second):
    def action(s, i):
        if i == 0:
            s.buy(qty=1, limit=80)
            before = state(s)
            with pytest.raises(ValueError):
                s.submit_oco(first=OrderRequest(side="buy", percent=20, stop=105), second=second)
            assert state(s) == before
            assert s.buy(qty=1, limit=80).order_id == "order-2"

    result = run(action, instrument=InstrumentSpec(price_tick=1), exclusive_orders=True)
    assert len(result._order_sizing) == 2
    assert result._order_sizing["mode"].tolist() == ["qty", "qty"]


@pytest.mark.parametrize("end", ["fill", "cancel", "expire", "reject"])
def test_mixed_oco_terminal_policies_and_traces(end):
    def action(s, i):
        if i == 0:
            s.group = s.submit_oco(
                first=OrderRequest(
                    side="buy",
                    percent=20,
                    stop=105,
                    expires_at=s.data_index[-1] if end == "expire" else None,
                ),
                second=OrderRequest(side="sell", amount=2000, stop=95),
            )
            if end == "cancel":
                s.group.cancel()

    result = run(action, max_gross_exposure=0.1 if end == "reject" else None)
    assert result._orders.status.tolist() == [
        {"fill": "Filled", "cancel": "Canceled", "expire": "Expired", "reject": "Rejected"}[end],
        "Canceled",
    ]
    assert result._order_sizing.qty.tolist() == [20, 20]
    if end == "fill":
        assert result._fills.qty.tolist() == [20]
        assert result.attrs["diagnostics"][0]["code"] == "ambiguous_oco_bar"
    else:
        assert result._fills.empty


def test_sizing_visible_in_events_internal_orders_and_reduce_only():
    class Script(Idle):
        def init(self):
            self.seen = []

        def next(self):
            if self.bar_index == 0:
                self.buy(amount=100, sl=50, tp=200)
            elif self.bar_index == 2:
                self.sell(qty=10, reduce_only=True)
            elif self.bar_index == 4:
                self.order_target_quantity(target=2)

        def on_order(self, event):
            order = next(
                o for o in self._broker.all_orders if o.order_id == event.snapshot.order_id
            )
            self.seen.append((order.order_id, order.sizing))

    result = Backtest(frame(), Script).run()
    sized = result._order_sizing
    assert sized.qty.tolist() == [1, 10]
    assert result._fills.qty.tolist() == [1, 1, 2]
    for order_id, snapshot in result._strategy.seen:
        if order_id in set(sized.order_id):
            assert snapshot.qty == sized.set_index("order_id").loc[order_id, "qty"]
        else:
            assert snapshot is None


def test_sizing_result_schema_empty_and_serialization():
    empty = Backtest(frame(), Idle).run()
    full = run(lambda s, i: s.buy(amount=2000, limit=95) if i == 0 else None)
    expected = ["order_id", "mode", "source", "value", "equity", "reference_price", "budget", "qty"]
    for result in (empty, full):
        table = result._order_sizing
        assert table.columns.tolist() == expected
        assert table.dtypes.astype(str).tolist() == ["string"] * 3 + ["float64"] * 5
        assert result.attrs["trading_schema_version"] == 4
        assert result.attrs["execution_policy_version"] == "2"
        pd.testing.assert_frame_equal(pickle.loads(pickle.dumps(table)), table)
        for key in ("_orders", "_order_events", "_fills"):
            assert result[key].columns.tolist() == empty[key].columns.tolist()
            assert result[key].dtypes.equals(empty[key].dtypes)


class ReusableSizing(Idle):
    request = OrderRequest(side="buy", percent=20, limit=1)

    def next(self):
        if self.bar_index == 0:
            self.submit_oco(first=self.request, second=OrderRequest(side="sell", qty=1, stop=50))


def sizing_process(args):
    request, cash = args
    result = Backtest(frame(), ReusableSizing, cash=cash).run(request=request)
    restored = pickle.loads(pickle.dumps(result))
    pd.testing.assert_frame_equal(restored._order_sizing, result._order_sizing)
    return request, restored._order_sizing


def test_sizing_request_and_results_cross_spawn_without_state_leak():
    request = OrderRequest(side="buy", percent=20, limit=1)
    with mp.get_context("spawn").Pool(1) as pool:
        first, second = pool.map(sizing_process, [(request, 10000), (request, 20000)])
    assert first[0] == second[0] == request
    assert first[1].qty.tolist() == [20, 1]
    assert second[1].qty.tolist() == [40, 1]
    first[1].loc[0, "qty"] = 999
    assert second[1].loc[0, "qty"] == 40 and request.percent == 20
