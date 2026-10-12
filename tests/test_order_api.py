"""Runtime contracts for author requests, explicit target arguments, and failure atomicity."""

import inspect
import pickle
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pandas as pd
import pytest
from test_trading_core import Idle, frame, run

from openbacktesting import Backtest, DefaultOrderSize, Strategy
from openbacktesting.broker import InstrumentSpec, OrderRequest
from openbacktesting.broker.models import NormalizedOrderRequest


def state(s):
    broker = s._broker
    return (
        dict(broker._counts),
        broker._sequence,
        tuple(broker.groups),
        tuple((o.order_id, o.snapshot) for o in broker.all_orders),
        tuple(broker.orders),
        tuple(broker.events),
        broker.account,
    )


def test_request_is_frozen_detached_and_pickle_safe():
    tag = {"purpose": ["突破"]}
    request = OrderRequest(
        side="buy",
        qty=2,
        limit=100,
        sl=90,
        tp=120,
        tag=tag,
        expires_at=datetime(2026, 1, 5, tzinfo=UTC),
    )
    tag["purpose"].append("modify")
    request.tag["purpose"].append("copy")
    assert request.tag == {"purpose": ["突破"]}
    assert request.expires_at == pd.Timestamp("2026-01-05T00:00Z")
    assert request.qty == 2 and request.stop is None and request.valid_bars is None
    assert not hasattr(request, "reduce_only") and not hasattr(request, "tag_json")
    with pytest.raises(FrozenInstanceError):
        request.qty = 3
    restored = pickle.loads(pickle.dumps(request))
    assert restored == request and restored.tag == request.tag
    with pytest.raises(AttributeError, match="OrderRequest"):
        pickle.loads(b"copenbacktesting.broker.models\nOrderRequest\n.")


@pytest.mark.parametrize(
    "values",
    [
        {"side": "other"},
        {"qty": 0},
        {"qty": -1},
        {"qty": True},
        {"qty": "1"},
        {"qty": float("inf")},
        {"limit": -1},
        {"stop": float("nan")},
        {"sl": False},
        {"tp": "120"},
        {"valid_bars": 0},
        {"valid_bars": True},
        {"valid_bars": 1.5},
        {"expires_at": "2026-01-05"},
        {"expires_at": pd.NaT},
        {"expires_at": "NaT"},
        {"expires_at": 123},
        {"expires_at": "bad"},
        {"expires_at": "2026-01-05T00:00Z", "valid_bars": 2},
        {"tag": object()},
        {"tag": (1, 2)},
        {"tag": {1: "x"}},
        {"tag": [float("nan")]},
    ],
)
def test_request_rejects_invalid_values(values):
    with pytest.raises((TypeError, ValueError)):
        OrderRequest(**({"side": "buy", "qty": 1} | values))


@pytest.mark.parametrize(
    "args,kwargs",
    [
        (("buy", 1), {}),
        ((), {"qty": 1}),
        ((), {"side": "buy"}),
        ((), {"side": "buy", "qty": 1, "limti": 80}),
        ((), {"side": "buy", "qty": 1, "reduce_only": True}),
        ((), {"side": "buy", "qty": 1, "trade_id": "trade-1"}),
        ((), {"side": "buy", "qty": 1, "tag_json": "null"}),
    ],
)
def test_request_constructor_has_only_author_keywords(args, kwargs):
    with pytest.raises(TypeError):
        OrderRequest(*args, **kwargs)


def test_request_reuse_in_init_and_independent_runs():
    request = OrderRequest(side="buy", qty=1, stop=105, tag=["突破"])

    class Script(Idle):
        def init(self):
            self.prepared = request
            self.other = OrderRequest(side="sell", qty=1, stop=80)
            before = state(self)
            with pytest.raises(RuntimeError):
                self.submit_oco(first=request, second=self.other)
            assert state(self) == before

        def next(self):
            if self.bar_index == 0:
                self.group = self.submit_oco(first=self.prepared, second=self.other)

    results = [
        Backtest(frame(), Script, default_order_size=DefaultOrderSize("fixed", 10)).run()
        for _ in range(2)
    ]
    pd.testing.assert_frame_equal(results[0]._orders, results[1]._orders)
    assert results[0]._fills.qty.tolist() == [1]
    order = results[0]._strategy.group.orders[0]
    assert isinstance(order.request, NormalizedOrderRequest)
    assert order.request.tag == ["突破"] and order.request is not request
    assert pickle.loads(pickle.dumps(order.request)) == order.request
    restored = pickle.loads(pickle.dumps(results[0]._orders))
    pd.testing.assert_frame_equal(restored, results[0]._orders)
    assert not hasattr(request, "order_id")


@pytest.mark.parametrize(
    "second",
    [
        OrderRequest(side="sell", qty=0.5),
        OrderRequest(side="sell", qty=1, sl=90),
        OrderRequest(side="sell", qty=1, tp=110),
        OrderRequest(side="sell", qty=1, limit=100.5),
    ],
)
def test_oco_context_failure_is_atomic(second):
    def action(s, i):
        if i == 0:
            pending = s.buy(qty=1, limit=80)
            before = state(s)
            with pytest.raises(ValueError):
                s.submit_oco(first=OrderRequest(side="buy", qty=1, limit=80), second=second)
            assert state(s) == before and pending.status == "Accepted"
            assert s.buy(qty=1, limit=80).order_id == "order-2"

    assert run(action, instrument=InstrumentSpec(price_tick=1))._fills.empty


@pytest.mark.parametrize("which", ["first", "second"])
def test_oco_rejects_non_request_members(which):
    def action(s, i):
        if i == 0:
            members = {
                "first": OrderRequest(side="buy", qty=1),
                "second": OrderRequest(side="sell", qty=1),
            }
            members[which] = {"side": "buy", "qty": 1}
            before = state(s)
            with pytest.raises(TypeError):
                s.submit_oco(**members)
            assert state(s) == before

    assert run(action)._orders.empty


def test_oco_same_direction_ordering_and_argument_binding():
    first = OrderRequest(side="buy", qty=1, limit=100)
    second = OrderRequest(side="buy", qty=2, limit=100)

    def action(s, i):
        if i == 0:
            before = state(s)
            for args, kwargs in [
                ((first, second), {}),
                ((), {"first": first}),
                ((), {"requests": [first, second]}),
                ((), {"first": first, "second": second, "third": first}),
            ]:
                with pytest.raises(TypeError):
                    s.submit_oco(*args, **kwargs)
                assert state(s) == before
            s.group = s.submit_oco(first=first, second=second)

    result = run(action)
    assert result._fills.qty.tolist() == [1]
    assert [o.request.qty for o in result._strategy.group.orders] == [1, 2]
    assert result.attrs["diagnostics"][0]["code"] == "ambiguous_oco_bar"


TARGETS = ("order_target_quantity", "order_target_value", "order_target_percent")


def test_target_signatures_are_explicit_and_consistent():
    signatures = [inspect.signature(getattr(Strategy, name)) for name in TARGETS]
    assert signatures[0] == signatures[1] == signatures[2]
    parameters = list(signatures[0].parameters.values())[1:]
    assert [p.name for p in parameters] == [
        "target",
        "limit",
        "stop",
        "sl",
        "tp",
        "tag",
        "reduce_only",
        "expires_at",
        "valid_bars",
    ]
    assert all(p.kind == inspect.Parameter.KEYWORD_ONLY for p in parameters)


@pytest.mark.parametrize("method", TARGETS)
@pytest.mark.parametrize("target", [0, 1])
def test_target_rejects_wrong_binding_even_without_an_order(method, target):
    def action(s, i):
        if i == 0:
            call = getattr(s, method)
            before = state(s)
            for args, kwargs in [((target,), {}), ((), {})] + [
                ((), {"target": target, field: 1})
                for field in ("limti", "conditions", "qty", "side", "trade")
            ]:
                with pytest.raises(TypeError):
                    call(*args, **kwargs)
                assert state(s) == before

    assert run(action)._orders.empty


@pytest.mark.parametrize("method", TARGETS)
@pytest.mark.parametrize("target", [0, 1])
@pytest.mark.parametrize(
    "conditions",
    [
        {"limit": -1},
        {"stop": 100.5},
        {"sl": float("nan")},
        {"tp": False},
        {"valid_bars": 0},
        {"valid_bars": True},
        {"valid_bars": 1.5},
        {"expires_at": "2026-01-05"},
        {"expires_at": pd.NaT},
        {"expires_at": "2026-01-05T00:00Z", "valid_bars": 1},
        {"tag": object()},
        {"tag": {1: "x"}},
        {"tag": [float("inf")]},
        {"reduce_only": 1},
        {"reduce_only": "false"},
    ],
)
def test_target_validation_precedes_all_side_effects(method, target, conditions):
    def action(s, i):
        if i == 0:
            old = s.order_target_quantity(target=2, limit=80)
            before = state(s)
            # A cash target of 1 rounds to zero; use 100 to test the nonzero branch too.
            actual_target = 100 if method == "order_target_value" and target else target
            with pytest.raises((TypeError, ValueError)):
                getattr(s, method)(target=actual_target, **conditions)
            assert state(s) == before and old.status == "Accepted"

    result = run(action, instrument=InstrumentSpec(price_tick=1))
    assert len(result._orders) == 1 and result._fills.empty


@pytest.mark.parametrize("method", TARGETS)
@pytest.mark.parametrize("index", [pd.RangeIndex(7), pd.date_range("2026-01-01", periods=7)])
def test_target_noop_checks_expiry_index_timezone(method, index):
    def action(s, i):
        if i == 0:
            before = state(s)
            with pytest.raises(ValueError, match="timezone"):
                getattr(s, method)(target=0, expires_at="2026-01-05T00:00Z")
            assert state(s) == before

    data = frame()
    data.index = index
    assert run(action, data=data)._orders.empty


@pytest.mark.parametrize("method", TARGETS)
def test_target_noop_and_directional_validation(method):
    def action(s, i):
        if i == 0:
            call = getattr(s, method)
            assert call(target=0, sl=110, tp=90, tag=["No order needed"]) is None
            before = state(s)
            for conditions in ({"sl": 110}, {"tp": 90}):
                with pytest.raises(ValueError, match="direction"):
                    call(target=100 if method == "order_target_value" else 1, **conditions)
                assert state(s) == before

    assert run(action)._orders.empty


def test_target_defaults_deduplicate_and_valid_noop_cancels_old():
    def action(s, i):
        if i == 0:
            old = s.order_target_quantity(target=1, limit=80)
            before = state(s)
            assert (
                s.order_target_quantity(
                    target=1,
                    limit=80,
                    stop=None,
                    sl=None,
                    tp=None,
                    tag=None,
                    reduce_only=False,
                    expires_at=None,
                    valid_bars=None,
                )
                is old
            )
            assert state(s) == before
            assert s.order_target_quantity(target=0, sl=110, tp=90) is None
            assert old.status == "Canceled" and len(s._broker.all_orders) == 1

    assert run(action)._orders.reason.tolist() == ["target_replaced"]


@pytest.mark.parametrize("method", ["buy", "sell"])
def test_regular_orders_reject_non_boolean_reduce_only(method):
    def action(s, i):
        if i == 0:
            before = state(s)
            with pytest.raises(TypeError, match="reduce_only"):
                getattr(s, method)(qty=1, reduce_only=1)
            assert state(s) == before

    assert run(action)._orders.empty
