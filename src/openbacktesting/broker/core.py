"""Single-asset trade scheduling: requests, execution facts, lots, and protection groups."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from math import copysign

import numpy as np
import pandas as pd

from openbacktesting.broker.commission import Commission, normalize_commission
from openbacktesting.broker.execution import Slippage, execution_price, match_price
from openbacktesting.broker.instrument import InstrumentSpec
from openbacktesting.broker.ledger import TradingLedger
from openbacktesting.broker.models import (
    ClosedTradeStats,
    Fill,
    NormalizedOrderRequest,
    OrderEvent,
    OrderSizingSnapshot,
    OrderSnapshot,
    OrderStatus,
    PositionSnapshot,
    TradeAllocation,
    finite,
    freeze_tag,
    record,
)
from openbacktesting.broker.requests import OrderRequest, _normalize_conditions
from openbacktesting.broker.sizing import resolve_size
from openbacktesting.helpers import _set_legacy_module

__pdoc__ = {"Order.__init__": False, "Trade.__init__": False, "Position.__init__": False}


class _OutOfMoneyError(Exception):
    pass


class Order:
    """Stable order handle; request and snapshot are immutable values, and cancel is repeatable."""

    def __init__(self, broker, request, *, group_id=None, kind="entry", eligible=None, sizing=None):
        self._broker = broker
        self._request_value = request
        self._sizing_value = sizing
        self._order_id = broker._id("order")
        self.group_id = group_id
        self.kind = kind
        self.ordinal = broker._counts["order"]
        self.created_bar = broker._i
        self.eligible_bar = broker._i + 1 if eligible is None else eligible
        self._snapshot = OrderSnapshot(
            self.order_id, OrderStatus.SUBMITTED, 0, request.qty, None, None, False
        )
        self.active_stop = request.stop
        self.trail = None
        self.target = None

    @property
    def order_id(self):
        """Stable, read-only order identity within each run."""
        return self._order_id

    @property
    def request(self) -> NormalizedOrderRequest:
        """The original normalized request cannot be replaced."""
        return self._request_value

    @property
    def snapshot(self) -> OrderSnapshot:
        """Latest frozen state, without exposing writable state."""
        return self._snapshot

    @property
    def sizing(self) -> OrderSizingSnapshot | None:
        """Sizing basis frozen at submission; None for targets, lot exits, and internal protection orders."""
        return self._sizing_value

    @property
    def status(self):
        """Current state; query events for historical states."""
        return self.snapshot.status

    @property
    def size(self):
        """Original signed asset quantity."""
        return self.request.qty * (1 if self.request.side == "buy" else -1)

    @property
    def limit(self):
        """Immutable requested limit price."""
        return self.request.limit

    @property
    def stop(self):
        """Currently effective trigger price; the original condition remains in request."""
        return self.active_stop

    @property
    def sl(self):
        """Initial requested stop-loss price."""
        return self.request.sl

    @property
    def tp(self):
        """Initial requested take-profit price."""
        return self.request.tp

    @property
    def group(self):
        """Associated OCO or protection group; None for ordinary standalone orders."""
        return self._broker.groups.get(self.group_id)

    @property
    def tag(self):
        """Independent plain-value copy of the user tag."""
        return self.request.tag

    @property
    def is_long(self):
        """Whether this is a buy-side request."""
        return self.size > 0

    @property
    def is_short(self):
        """Whether this is a sell-side request."""
        return self.size < 0

    @property
    def parent_trade(self):
        """Associated active lot; None after closure."""
        return next((t for t in self._broker.trades if t.trade_id == self.request.trade_id), None)

    @property
    def is_contingent(self):
        """Whether this is a lot protection exit."""
        return self.kind in ("sl", "tp", "trail")

    def cancel(self):
        """Cancel an unfinished order; calls on terminal states are idempotent."""
        if not self.status.terminal:
            self._broker._permission()
        self._broker.cancel(self, "user_canceled")
        return self.snapshot

    def __repr__(self):
        return f"<Order {self.order_id} size={self.size:g} status={self.status} tag={self.tag!r}>"


class OrderGroup:
    """Queryable OCO or lot protection group; cancellation does not close positions."""

    def __init__(self, broker, group_id, kind):
        self._broker = broker
        self.group_id = group_id
        self.kind = kind
        self._orders = []

    @property
    def orders(self):
        """All orders in this group, including historical terminal orders."""
        return tuple(self._orders)

    def cancel(self):
        """Cancel all still-active members without automatically exiting positions."""
        for order in self.orders:
            order.cancel()


class Trade:
    """Entry lot that can be exited and protected separately; partial exits preserve trade_id."""

    def __init__(
        self,
        broker,
        size,
        entry_price,
        entry_bar,
        tag=None,
        *,
        trade_id=None,
        entry_fill_id="",
        entry_fee=0,
        group_id=None,
    ):
        self._broker = broker
        self._size = size
        self.entry_price = entry_price
        self.entry_bar = entry_bar
        self.exit_price = None
        self.exit_bar = None
        self.trade_id = trade_id or broker._id("trade")
        self.entry_fill_id = entry_fill_id
        self.group_id = group_id
        self._tag_json = freeze_tag(tag)
        self._entry_commission = entry_fee
        self._exit_commission = 0.0
        self._sl_order = None
        self._tp_order = None
        self._closed_sl = self._closed_tp = None

    @property
    def size(self):
        """Signed quantity of the remaining or closed portion."""
        return self._size

    @property
    def group(self):
        """Lot protection group, including historical replaced members."""
        return self._broker.groups.get(self.group_id)

    @property
    def tag(self):
        """Copy of the entry tag."""
        import json

        return json.loads(self._tag_json)

    @property
    def entry_time(self):
        """Entry bar index."""
        return self._broker._index[self.entry_bar]

    @property
    def exit_time(self):
        """Closing bar index; None while active."""
        return None if self.exit_bar is None else self._broker._index[self.exit_bar]

    @property
    def is_long(self):
        """Whether this is a long lot."""
        return self.size > 0

    @property
    def is_short(self):
        """Whether this is a short lot."""
        return self.size < 0

    @property
    def _commissions(self):
        return self._entry_commission + self._exit_commission

    @property
    def pl_gross(self):
        """Gross price profit or loss."""
        price = self._broker.last_price if self.exit_price is None else self.exit_price
        return self.size * (price - self.entry_price)

    @property
    def pl(self):
        """Net profit or loss including allocated fees; active lots include remaining entry fees."""
        return self.pl_gross - self._commissions

    @property
    def return_fraction(self):
        """Net return fraction using remaining or allocated entry notional as the denominator."""
        return self.pl / (abs(self.size) * self.entry_price)

    @property
    def value(self):
        """Absolute notional value at the current or exit price."""
        price = self._broker.last_price if self.exit_price is None else self.exit_price
        return abs(self.size) * price

    @property
    def sl(self):
        """Current stop-loss price; writes record cancellation and replacement events."""
        return (
            self._sl_order.stop
            if self._sl_order is not None and not self._sl_order.status.terminal
            else self._closed_sl
        )

    @sl.setter
    def sl(self, price):
        self._broker.protect(self, "sl", price)

    @property
    def tp(self):
        """Current take-profit price; None cancels protection."""
        return (
            self._tp_order.limit
            if self._tp_order is not None and not self._tp_order.status.terminal
            else self._closed_tp
        )

    @tp.setter
    def tp(self, price):
        self._broker.protect(self, "tp", price)

    def close(self, portion=None, *, qty=None):
        """Reduce-only exit; qty and portion are mutually exclusive, and the default closes the entire lot."""
        if qty is not None and portion is not None:
            raise ValueError("qty and portion are mutually exclusive")
        if qty is None:
            portion = 1.0 if portion is None else finite(portion, "portion", positive=True)
            if portion > 1:
                raise ValueError("portion must not exceed 1")
            qty = self._broker.instrument.quantity(
                abs(self.size) * portion, floor=True, opening=False
            )
        else:
            qty = self._broker.instrument.quantity(qty, opening=False)
        if qty <= 0:
            raise ValueError("Closing quantity rounds to zero")
        return self._broker.new_order(
            qty, side="sell" if self.is_long else "buy", trade=self, reduce_only=True, tag=self.tag
        )

    def set_trailing_stop(self, *, amount=None, percent=None):
        """Create a native trailing stop, replacing the fixed SL; effective from the next eligible bar."""
        if (amount is None) == (percent is None):
            raise ValueError("Exactly one of amount and percent must be supplied")
        value = finite(amount if amount is not None else percent, "trail", positive=True)
        if percent is not None and value >= 1:
            raise ValueError("percent must be less than 1")
        distance = value if amount is not None else self._broker.last_price * value
        price = self._broker.instrument.price(
            self._broker.last_price - copysign(distance, self.size),
            side="sell" if self.is_long else "buy",
        )
        order = self._broker.protect(self, "sl", price, kind="trail")
        order.trail = ("amount" if amount is not None else "percent", value)
        return order

    def __repr__(self):
        return f"<Trade {self.trade_id} size={self.size:g} pl={self.pl:g} tag={self.tag}>"


class Position:
    """Aggregate active lots; truthiness depends on total exposure."""

    def __init__(self, broker):
        self._broker = broker

    @property
    def snapshot(self) -> PositionSnapshot:
        """Frozen snapshot of net position, gross exposure, and fees."""
        return self._broker.ledger.position(self._broker.trades, self._broker.last_price)

    @property
    def size(self):
        """Signed net quantity."""
        return self.snapshot.net_qty

    @property
    def pl(self):
        """Unrealized net profit or loss including remaining entry fees."""
        return self.snapshot.unrealized_pnl_net

    @property
    def return_fraction(self):
        """Net return fraction; None when a hedged or flat position has no common cost basis."""
        return self.snapshot.return_fraction

    @property
    def has_exposure(self):
        """Whether any lot is still held."""
        return self.snapshot.has_exposure

    @property
    def is_long(self):
        """Whether the net position is long."""
        return self.size > 0

    @property
    def is_short(self):
        """Whether the net position is short."""
        return self.size < 0

    def close(self, portion=None):
        """Submit reduce-only orders for each lot and return an ordered tuple."""
        return tuple(t.close(portion) for t in tuple(self._broker.trades))

    def __bool__(self):
        return self.has_exposure

    def __repr__(self):
        return f"<Position: {self.size:g} ({len(self._broker.trades)} trades)>"


class _Broker:
    def __init__(
        self,
        *,
        data,
        cash,
        spread,
        commission,
        margin,
        hedging=False,
        exclusive_orders=False,
        index,
        instrument=None,
        slippage=None,
        allow_short=True,
        max_gross_exposure=None,
        execution_timing="next_open",
    ):
        cash = finite(cash, "cash", positive=True)
        margin = finite(margin, "margin", positive=True)
        if margin > 1:
            raise ValueError("margin must not exceed 1")
        spread = finite(spread, "spread")
        if not 0 <= spread < 1:
            raise ValueError("spread must be in [0,1)")
        if max_gross_exposure is not None:
            max_gross_exposure = finite(max_gross_exposure, "max_gross_exposure", positive=True)
        self._data, self._index = data, index
        self.instrument = instrument or InstrumentSpec()
        self.slippage = slippage or Slippage()
        self.ledger = TradingLedger(cash)
        self.margin, self._spread = margin, spread
        self._hedging, self._exclusive_orders = hedging, exclusive_orders
        self.allow_short, self.max_gross_exposure = allow_short, max_gross_exposure
        self.execution_timing = execution_timing
        self._commission_model = commission
        if not callable(commission):
            self._linear_commission = normalize_commission(commission)
            if not isinstance(commission, Commission):
                self._commission_model = (
                    self._linear_commission.fixed,
                    self._linear_commission.relative,
                )
        self.orders, self.all_orders = [], []
        self.trades, self.closed_trades = [], []
        self._closed_stats = ClosedTradeStats()
        self.events, self.fills, self.allocations = [], [], []
        self.groups, self.diagnostics, self._notifications = {}, [], []
        self.account_curve, self.position_curve = [], []
        self._counts, self._sequence = {}, 0
        self._i, self.phase = 0, "init"
        self._equity = np.full(len(index), float(cash))
        self._exposure = np.zeros(len(index), dtype=bool)
        self.position = Position(self)
        self._target_order = None
        self.observations = None

    def _commission_func(self, *args):
        raise TypeError("Trading state from 0.1 cannot resume execution; rerun the backtest with a 0.2 configuration")

    def _commission(self, qty, price):
        if callable(self._commission_model):
            return self._commission_model(qty, price)
        return self._linear_commission.calculate(qty, price)

    def order_target(self, target, conditions):
        self._permission()
        if self._hedging:
            raise ValueError("Target positions do not support hedging mode")
        target = finite(target, "target")
        target = copysign(self.instrument.quantity(abs(target), floor=True, opening=False), target)
        if target < 0 and not self.allow_short:
            raise ValueError("short_not_allowed")
        old = self._target_order
        if any(o is not old and not o.is_contingent for o in self.orders):
            raise ValueError("conflicting_pending_order")
        delta = float(Decimal(str(target)) - Decimal(str(self.position.size)))
        identity_values = self._conditions(**conditions)
        if identity_values.get("expires_at") is not None:
            identity_values["expires_at"] = pd.Timestamp(identity_values["expires_at"]).isoformat()
        identity = (target, freeze_tag(identity_values))
        # Validate the new request first; invalid reuse or replacement must not alter a valid existing intent.
        request = (
            None
            if delta == 0
            else self._request(abs(delta), side="buy" if delta > 0 else "sell", **conditions)
        )
        if old is not None and not old.status.terminal and old.target == identity:
            return old
        if old is not None and not old.status.terminal:
            self.cancel(old, "target_replaced")
        if request is None:
            self._target_order = None
            return None
        order = self.new_order(request.qty, side=request.side, **conditions)
        order.target = identity
        self._target_order = order
        return order

    def _id(self, kind):
        self._counts[kind] = self._counts.get(kind, 0) + 1
        return f"{kind}-{self._counts[kind]}"

    def _seq(self):
        self._sequence += 1
        return self._sequence

    @property
    def last_price(self):
        return self._data._current_value("Close")

    @property
    def account(self):
        return self.ledger.account(self.position.snapshot, self.margin)

    @property
    def equity(self):
        price = self.last_price
        return self.ledger.balance + sum(t.size * (price - t.entry_price) for t in self.trades)

    @property
    def margin_available(self):
        return self.account.margin_available

    @property
    def _cash(self):
        return self.ledger.balance

    def _permission(self):
        if self.phase not in ("next", "notify"):
            raise RuntimeError("Trading commands are prohibited during this lifecycle phase")

    def _event(self, order):
        event = OrderEvent(self._seq(), self._i, self._index[self._i], self.phase, order.snapshot)
        self.events.append(event)
        self._notifications.append(event)

    def _state(self, order, status, reason=None, **changes):
        if order.status.terminal:
            return
        order._snapshot = replace(order.snapshot, status=status, reason=reason, **changes)
        self._event(order)
        if status.terminal:
            self.orders.remove(order)
            group = self.groups.get(order.group_id)
            if group is not None and group.kind == "oco":
                for peer in group.orders:
                    if peer is not order and not peer.status.terminal:
                        self._state(
                            peer,
                            OrderStatus.CANCELED,
                            "oco_peer_filled"
                            if status == OrderStatus.FILLED
                            else "oco_peer_terminated",
                        )

    def cancel(self, order, reason):
        self._state(order, OrderStatus.CANCELED, reason)

    def _conditions(self, **conditions):
        values = _normalize_conditions(**conditions)
        for name in ("limit", "stop", "sl", "tp"):
            if values[name] is not None:
                self.instrument.price(values[name])
        if values["expires_at"] is not None and (
            not isinstance(self._index, pd.DatetimeIndex) or self._index.tz is None
        ):
            raise ValueError("Absolute expiration and market-data index must be timezone-aware")
        return values

    def _request(
        self,
        qty,
        *,
        side,
        limit=None,
        stop=None,
        sl=None,
        tp=None,
        tag=None,
        trade=None,
        reduce_only=False,
        expires_at=None,
        valid_bars=None,
    ):
        if side not in ("buy", "sell"):
            raise ValueError("side must be buy/sell")
        conditions = self._conditions(
            limit=limit,
            stop=stop,
            sl=sl,
            tp=tp,
            tag=tag,
            reduce_only=reduce_only,
            expires_at=expires_at,
            valid_bars=valid_bars,
        )
        qty = self.instrument.quantity(qty, opening=not reduce_only)
        if qty <= 0:
            raise ValueError("qty must be positive")
        if self._hedging and reduce_only and trade is None:
            raise ValueError("Hedged reduce-only orders must reference a trade")
        reference = limit or stop or self.last_price
        if sl is not None and ((sl >= reference) if side == "buy" else (sl <= reference)):
            raise ValueError("Invalid SL direction")
        if tp is not None and ((tp <= reference) if side == "buy" else (tp >= reference)):
            raise ValueError("Invalid TP direction")
        return NormalizedOrderRequest(
            side=side,
            qty=qty,
            trade_id=trade.trade_id if trade is not None else None,
            **conditions,
        )

    def _submit(self, request, *, group_id=None, kind="entry", eligible=None, sizing=None):
        order = Order(self, request, group_id=group_id, kind=kind, eligible=eligible, sizing=sizing)
        self.all_orders.append(order)
        if group_id is not None:
            self.groups[group_id]._orders.append(order)
        self.orders.append(order)
        self._event(order)
        if request.expires_at is not None and self._index[self._i] >= request.expires_at:
            self._state(order, OrderStatus.EXPIRED, "expired")
        else:
            self._state(order, OrderStatus.ACCEPTED)
        return order

    def submit_order(self, intent, *, side, reduce_only=False, **kwargs):
        self._permission()
        sizing = resolve_size(
            intent,
            account=self.account,
            reference_price=self.last_price,
            instrument=self.instrument,
            reduce_only=reduce_only,
        )
        return self.new_order(
            sizing.qty, side=side, reduce_only=reduce_only, _sizing=sizing, **kwargs
        )

    def new_order(
        self,
        qty,
        *,
        side,
        _internal=False,
        _group=None,
        _kind="entry",
        _eligible=None,
        _sizing=None,
        **kwargs,
    ):
        if not _internal:
            self._permission()
        request = self._request(qty, side=side, **kwargs)
        if self._exclusive_orders and not request.reduce_only and not _internal:
            for order in tuple(self.orders):
                if not order.request.reduce_only:
                    self.cancel(order, "exclusive_replaced")
            self.position.close()
        if _group is None and (request.sl is not None or request.tp is not None):
            _group = self._id("group")
            self.groups[_group] = OrderGroup(self, _group, "bracket")
        if (
            _eligible is None
            and self.execution_timing == "same_close"
            and self.phase == "next"
            and request.limit is None
            and request.stop is None
        ):
            _eligible = self._i
        return self._submit(
            request, group_id=_group, kind=_kind, eligible=_eligible, sizing=_sizing
        )

    def submit_oco(self, *, first: OrderRequest, second: OrderRequest) -> OrderGroup:
        self._permission()
        if not isinstance(first, OrderRequest) or not isinstance(second, OrderRequest):
            raise TypeError("OCO first and second must be OrderRequest instances")
        context = {
            "account": self.account,
            "reference_price": self.last_price,
            "instrument": self.instrument,
        }
        prepared = []
        for item in (first, second):
            sizing = resolve_size(item._size, **context)
            request = self._request(
                qty=sizing.qty,
                **{
                    name: getattr(item, name)
                    for name in (
                        "side",
                        "limit",
                        "stop",
                        "sl",
                        "tp",
                        "tag",
                        "expires_at",
                        "valid_bars",
                    )
                },
            )
            prepared.append((request, sizing))
        group_id = self._id("group")
        group = self.groups[group_id] = OrderGroup(self, group_id, "oco")
        members = [self._submit(r, group_id=group_id, sizing=s) for r, s in prepared]
        if any(o.status.terminal for o in members):
            group.cancel()
        return group

    def protect(self, trade, which, price, *, kind=None, eligible=None):
        if self.phase not in ("execute", "close", "terminal"):
            self._permission()
        if trade not in self.trades:
            raise ValueError("Protection can only be created for active lots")
        if price is not None:
            self.instrument.price(price)
        attr = "_sl_order" if which == "sl" else "_tp_order"
        old = getattr(trade, attr)
        if old is not None:
            self.cancel(old, "protection_replaced")
        setattr(trade, attr, None)
        if price is None:
            return None
        if trade.group_id is None:
            trade.group_id = self._id("group")
            self.groups[trade.group_id] = OrderGroup(self, trade.group_id, "bracket")
        params = {"stop": price} if which == "sl" else {"limit": price}
        order = self.new_order(
            abs(trade.size),
            side="sell" if trade.is_long else "buy",
            trade=trade,
            reduce_only=True,
            tag=trade.tag,
            _internal=True,
            _group=trade.group_id,
            _kind=kind or which,
            _eligible=eligible,
            **params,
        )
        setattr(trade, attr, order)
        return order

    def _expire(self):
        for order in tuple(self.orders):
            request = order.request
            if (request.expires_at is not None and self._index[self._i] >= request.expires_at) or (
                request.valid_bars is not None and self._i > order.created_bar + request.valid_bars
            ):
                self._state(order, OrderStatus.EXPIRED, "expired")

    def _plan(self, order, qty):
        candidates = [t for t in self.trades if t.size * order.size < 0]
        if order.request.trade_id:
            candidates = [t for t in candidates if t.trade_id == order.request.trade_id]
        if self._hedging and not order.request.reduce_only:
            candidates = []
        plan, left = [], qty
        for trade in candidates:
            used = min(abs(trade.size), left)
            plan.append((trade, used))
            left = float(Decimal(str(left)) - Decimal(str(used)))
            if left == 0:
                break
        return plan, left

    def _execute(self, order, base, *, phase="execute", reason="execution", bounds=None):
        request = order.request
        qty = request.qty
        plan, opening = self._plan(order, qty)
        if request.reduce_only:
            qty = float(Decimal(str(qty)) - Decimal(str(opening)))
            opening = 0
            if qty <= 0:
                self.cancel(order, "no_position")
                return
        price = execution_price(
            base,
            request.side,
            spread=self._spread,
            slippage=self.slippage,
            instrument=self.instrument,
            limit=request.limit,
            bounds=bounds,
        )
        if price is None:
            return
        sign = 1 if order.is_long else -1
        fee = finite(self._commission(sign * qty, price), "commission")
        realized = sum(copysign(used, t.size) * (price - t.entry_price) for t, used in plan)
        if not request.reduce_only:
            position = self.ledger.position(self.trades, base)
            remaining_pl = position.unrealized_pnl_gross - sum(
                copysign(used, t.size) * (base - t.entry_price) for t, used in plan
            )
            equity = (
                self.ledger.balance
                + realized
                - fee
                + remaining_pl
                + sign * opening * (base - price)
            )
            gross = (position.gross_qty - sum(q for _, q in plan) + opening) * base
            rejection = None
            if opening and sign < 0 and not self.allow_short:
                rejection = "short_not_allowed"
            elif opening and opening < self.instrument.min_quantity:
                rejection = "min_quantity"
            elif opening and opening * price < self.instrument.min_notional:
                rejection = "min_notional"
            elif opening and (equity <= 0 or gross * self.margin > equity):
                rejection = "insufficient_funds"
            elif (
                opening
                and self.max_gross_exposure is not None
                and gross > self.max_gross_exposure * equity
            ):
                rejection = "gross_exposure_limit"
            if rejection:
                self._state(order, OrderStatus.REJECTED, rejection)
                return
        if self.observations is not None:
            self.observations.before(
                self, base, phase, request.limit is not None or request.stop is not None
            )
        fill = Fill(
            self._id("fill"),
            order.order_id,
            self._seq(),
            request.side,
            qty,
            price,
            fee,
            self._i,
            self._index[self._i],
            phase,
            reason,
        )
        self.fills.append(fill)
        self._notifications.append(fill)
        fee_left = fee
        for number, (trade, used) in enumerate(plan):
            allocated_fee = (
                fee_left if not opening and number == len(plan) - 1 else fee * used / qty
            )
            fee_left -= allocated_fee
            self._close_piece(trade, used, price, allocated_fee, fill)
        if opening:
            trade = Trade(
                self,
                sign * opening,
                price,
                self._i,
                request.tag,
                entry_fill_id=fill.fill_id,
                entry_fee=fee_left,
                group_id=order.group_id
                if self.groups.get(order.group_id) is not None
                and self.groups[order.group_id].kind == "bracket"
                else None,
            )
            self.trades.append(trade)
            if self.observations is not None:
                self.observations.opened(
                    self, trade, request.limit is not None or request.stop is not None, phase
                )
            self.allocations.append(
                TradeAllocation(
                    self._id("allocation"),
                    fill.fill_id,
                    trade.trade_id,
                    fill.fill_id,
                    "open",
                    opening,
                    fee_left,
                    0,
                    0,
                )
            )
            eligible = (
                self._i
                if phase == "execute" and request.limit is None and request.stop is None
                else self._i + 1
            )
            if request.tp is not None:
                self.protect(trade, "tp", request.tp, eligible=eligible)
            if request.sl is not None:
                self.protect(trade, "sl", request.sl, eligible=eligible)
            if eligible > self._i and (request.sl is not None or request.tp is not None):
                self.diagnostics.append(
                    {
                        "code": "protection_next_bar",
                        "order_id": order.order_id,
                        "bar_index": self._i,
                    }
                )
        self.ledger.apply(realized, fee)
        if self.observations is not None:
            self.observations.sample(self, base, "after_" + phase)
        remaining = float(Decimal(str(request.qty)) - Decimal(str(qty)))
        self._state(
            order,
            OrderStatus.PARTIALLY_FILLED if remaining else OrderStatus.FILLED,
            filled_qty=qty,
            remaining_qty=remaining,
            avg_fill_price=price,
        )
        if remaining:
            self.cancel(order, "reduce_only_remainder")

    def _close_piece(self, trade, qty, price, fee, fill):
        original = abs(trade.size)
        entry_fee = (
            trade._entry_commission if qty == original else trade._entry_commission * qty / original
        )
        piece = Trade(
            self,
            copysign(qty, trade.size),
            trade.entry_price,
            trade.entry_bar,
            trade.tag,
            trade_id=trade.trade_id,
            entry_fill_id=trade.entry_fill_id,
            entry_fee=entry_fee,
            group_id=trade.group_id,
        )
        piece._closed_sl, piece._closed_tp = trade.sl, trade.tp
        piece.exit_price, piece.exit_bar, piece._exit_commission = price, self._i, fee
        self.closed_trades.append(piece)
        self.allocations.append(
            TradeAllocation(
                self._id("allocation"),
                fill.fill_id,
                trade.trade_id,
                trade.entry_fill_id,
                "close",
                qty,
                fee,
                entry_fee,
                piece.pl_gross,
            )
        )
        piece.allocation_id = self.allocations[-1].allocation_id
        piece.exit_fill_id = fill.fill_id
        piece.exit_sequence = fill.sequence
        if self.observations is not None:
            self.observations.close(trade, piece.allocation_id)
        previous = self._closed_stats
        pnl = piece.pl
        count = previous.closed_count + 1
        wins = previous.win_count + int(pnl > 0)
        winning = previous.winning_profit + max(pnl, 0.0)
        losing = previous.losing_amount + max(-pnl, 0.0)
        net = winning - losing
        self._closed_stats = ClosedTradeStats(
            closed_count=count,
            win_count=wins,
            loss_count=previous.loss_count + int(pnl < 0),
            even_count=previous.even_count + int(pnl == 0),
            winning_profit=winning,
            losing_amount=losing,
            net_profit=net,
            average_profit=net / count,
            win_rate=wins / count,
        )
        protection = [("sl", trade._sl_order), ("tp", trade._tp_order)]
        trade._entry_commission -= entry_fee
        if qty == original:
            self.trades.remove(trade)
            for _, old in protection:
                if old is not None and old.order_id != fill.order_id:
                    self.cancel(old, "position_closed")
        else:
            trade._size = copysign(float(Decimal(str(original)) - Decimal(str(qty))), trade.size)
            for which, old in protection:
                if old is not None and not old.status.terminal:
                    new = self.protect(
                        trade,
                        which,
                        old.stop if which == "sl" else old.limit,
                        kind=old.kind,
                        eligible=old.eligible_bar,
                    )
                    new.trail = old.trail

    def _protect_ambiguity(self, order, open_, high, low):
        if order.kind not in ("sl", "trail"):
            return
        trade = order.parent_trade
        if trade is not None and trade._tp_order is not None:
            peer = trade._tp_order
            if (
                not peer.status.terminal
                and peer.eligible_bar <= self._i
                and match_price(peer.request, triggered=False, open_=open_, high=high, low=low)[0]
                is not None
            ):
                self.diagnostics.append(
                    {
                        "code": "ambiguous_bracket_bar",
                        "order_id": order.order_id,
                        "bar_index": self._i,
                    }
                )

    def process(self, *, close=False):
        if close and self.observations is not None:
            self.observations.bar(self)
        self.phase = "close" if close else "execute"
        self._expire()
        if not self.orders:
            return
        open_, high, low = (self._data._current_value(name) for name in ("Open", "High", "Low"))
        candidates = sorted(self.orders, key=lambda o: (o.kind not in ("sl", "trail"), o.ordinal))
        processed = set()
        for order in candidates:
            if order.status.terminal or order.eligible_bar > self._i:
                continue
            if close and (
                order.created_bar != self._i or order.limit is not None or order.stop is not None
            ):
                continue
            request = replace(order.request, stop=order.active_stop)
            base, triggered = (
                (self.last_price, False)
                if close
                else match_price(
                    request, triggered=order.snapshot.triggered, open_=open_, high=high, low=low
                )
            )
            if triggered and not order.snapshot.triggered:
                order._snapshot = replace(order.snapshot, triggered=True)
                self._event(order)
            if base is None:
                continue
            group = self.groups.get(order.group_id)
            if group is not None and group.kind == "oco":
                peers = [p for p in group.orders if p is not order and not p.status.terminal]
                if any(
                    match_price(
                        p.request, triggered=p.snapshot.triggered, open_=open_, high=high, low=low
                    )[0]
                    is not None
                    for p in peers
                ):
                    self.diagnostics.append(
                        {
                            "code": "ambiguous_oco_bar",
                            "order_id": order.order_id,
                            "bar_index": self._i,
                        }
                    )
            if not close:
                self._protect_ambiguity(order, open_, high, low)
            self._execute(order, base, phase=self.phase, bounds=None if close else (low, high))
            processed.add(order.order_id)
        # Process only protection orders created by market entries in this phase; do not re-execute ordinary requests.
        if not close:
            for order in sorted(self.orders, key=lambda o: o.kind not in ("sl", "trail")):
                if (
                    order.status.terminal
                    or not order.is_contingent
                    or order.order_id in processed
                    or order.eligible_bar > self._i
                ):
                    continue
                base, _ = match_price(
                    order.request, triggered=False, open_=open_, high=high, low=low
                )
                if base is not None:
                    self._protect_ambiguity(order, open_, high, low)
                    self._execute(order, base, bounds=(low, high))

    def update_trails(self):
        for order in tuple(self.orders):
            if order.trail is None:
                continue
            mode, value = order.trail
            distance = value if mode == "amount" else self.last_price * value
            candidate = self.last_price + (distance if order.is_long else -distance)
            candidate = self.instrument.price(candidate, side="buy" if order.is_long else "sell")
            order.active_stop = (
                min(order.active_stop, candidate)
                if order.is_long
                else max(order.active_stop, candidate)
            )
            order.eligible_bar = max(order.eligible_bar, self._i + 1)

    def capture(self, phase="bar"):
        position = self.position.snapshot
        account = self.ledger.account(position, self.margin)
        prefix = {"bar_index": self._i, "timestamp": self._index[self._i], "phase": phase}
        account_values, position_values = record(account), record(position)
        self.account_curve.append(prefix | account_values)
        self.position_curve.append(prefix | position_values)
        if self.observations is not None:
            eligible = phase == "bar" and self.execution_timing != "same_close"
            if eligible:
                self.observations.mark_bar(self)
            self.observations.sample(
                self,
                self.last_price,
                phase,
                facts=account_values | position_values,
                range_eligible=eligible and self.observations.changed_bar != self._i,
            )
        self._equity[self._i] = account.equity
        if phase == "bar":
            self._exposure[self._i] = position.has_exposure

    def finish(self, *, liquidate, reason="end_of_data"):
        self.phase = "terminal"
        for order in tuple(self.orders):
            self.cancel(order, reason)
        if liquidate:
            for trade in tuple(self.trades):
                order = self.new_order(
                    abs(trade.size),
                    side="sell" if trade.is_long else "buy",
                    trade=trade,
                    reduce_only=True,
                    _internal=True,
                    _eligible=self._i,
                )
                self._execute(
                    order,
                    self.last_price,
                    phase="terminal",
                    reason="end_liquidation" if reason == "end_of_data" else reason,
                )
        self.capture("terminal")

    def __repr__(self):
        return f"<Broker: {self.equity:g} ({len(self.trades)} trades)>"


for _type in (Position, _OutOfMoneyError, Order, Trade, _Broker):
    _set_legacy_module(_type, "openbacktesting.engine")
