"""从交易事实生成固定列的纯值结果表。"""

from dataclasses import asdict
from importlib.metadata import version

import numpy as np
import pandas as pd

from openbacktesting.broker.commission import Commission
from openbacktesting.broker.models import (
    AccountSnapshot,
    Fill,
    NormalizedOrderRequest,
    OrderSizingSnapshot,
    OrderSnapshot,
    PositionSnapshot,
    TradeAllocation,
    columns,
    record,
)

_FLOAT_FIELDS = {
    "value",
    "reference_price",
    "budget",
    "qty",
    "price",
    "fee",
    "filled_qty",
    "remaining_qty",
    "avg_fill_price",
    "limit",
    "stop",
    "sl",
    "tp",
    "entry_fee",
    "realized_pnl_gross",
    "balance",
    "equity",
    "unrealized_pnl_gross",
    "fees_paid",
    "margin_used",
    "margin_available",
    "gross_notional",
    "net_notional",
    "net_qty",
    "gross_qty",
    "long_qty",
    "short_qty",
    "long_avg_price",
    "short_avg_price",
    "avg_price",
    "unrealized_pnl_net",
    "entry_fees_remaining",
    "return_fraction",
    "Size",
    "EntryPrice",
    "EntryFeeRemaining",
    "PnLGross",
    "PnL",
    "ReturnPct",
}
_INT_FIELDS = {"bar_index", "created_bar", "sequence", "EntryBar"}
_BOOL_FIELDS = {"triggered", "reduce_only"}
_OBJECT_FIELDS = {"timestamp", "expires_at", "EntryTime", "Tag"}


def _table(rows, *, columns):
    # 按目标dtype一次构造列，避免先推断再逐列转换/替换整个DataFrame的块。
    data = {}
    for name in columns:
        values = [row.get(name) for row in rows]
        if name in _FLOAT_FIELDS:
            data[name] = np.asarray(values, dtype="float64")
        elif name in _INT_FIELDS:
            data[name] = np.asarray(values, dtype="int64")
        elif name in _BOOL_FIELDS:
            data[name] = np.asarray(values, dtype=bool)
        elif name in _OBJECT_FIELDS:
            # Series保留object；直接传数组会使DataFrame再次推断时间/嵌套标签。
            data[name] = pd.Series(values, dtype="object")
        else:
            data[name] = pd.array(values, dtype="Int64" if name == "valid_bars" else "string")
    return pd.DataFrame(data, columns=columns)


def trading_results(stats, broker, end_policy):
    """附加账本表及可追溯配置，不依赖_strategy读取交易记录。"""
    original = stats
    stats = dict(stats)
    order_columns = (
        columns(OrderSnapshot)
        + columns(NormalizedOrderRequest)
        + ["group_id", "kind", "created_bar"]
    )
    stats["_orders"] = _table(
        [
            record(o.snapshot)
            | record(o.request)
            | {"group_id": o.group_id, "kind": o.kind, "created_bar": o.created_bar}
            for o in broker.all_orders
        ],
        columns=order_columns,
    )
    stats["_order_sizing"] = _table(
        [
            {"order_id": o.order_id} | record(o.sizing)
            for o in broker.all_orders
            if o.sizing is not None
        ],
        columns=["order_id"] + columns(OrderSizingSnapshot),
    )
    event_columns = ["sequence", "bar_index", "timestamp", "phase"] + columns(OrderSnapshot)
    stats["_order_events"] = _table(
        [
            {
                "sequence": e.sequence,
                "bar_index": e.bar_index,
                "timestamp": e.timestamp,
                "phase": e.phase,
            }
            | record(e.snapshot)
            for e in broker.events
        ],
        columns=event_columns,
    )
    for name, records, model in (
        ("_fills", broker.fills, Fill),
        ("_trade_allocations", broker.allocations, TradeAllocation),
    ):
        stats[name] = _table([record(item) for item in records], columns=columns(model))
    prefix = ["bar_index", "timestamp", "phase"]
    stats["_positions"] = _table(broker.position_curve, columns=prefix + columns(PositionSnapshot))
    stats["_account_curve"] = _table(
        broker.account_curve, columns=prefix + columns(AccountSnapshot)
    )
    stats["_final_account"] = record(broker.account)
    stats["_open_trades"] = _table(
        [
            {
                "trade_id": t.trade_id,
                "entry_fill_id": t.entry_fill_id,
                "Size": t.size,
                "EntryPrice": t.entry_price,
                "EntryBar": t.entry_bar,
                "EntryTime": t.entry_time,
                "EntryFeeRemaining": t._entry_commission,
                "PnLGross": t.pl_gross,
                "PnL": t.pl,
                "ReturnPct": t.return_fraction,
                "Tag": t.tag,
            }
            for t in broker.trades
        ],
        columns=[
            "trade_id",
            "entry_fill_id",
            "Size",
            "EntryPrice",
            "EntryBar",
            "EntryTime",
            "EntryFeeRemaining",
            "PnLGross",
            "PnL",
            "ReturnPct",
            "Tag",
        ],
    )
    stats["_trades"]["trade_id"] = pd.Series(
        [t.trade_id for t in broker.closed_trades], dtype="string"
    )
    stats["_trades"]["entry_fill_id"] = pd.Series(
        [t.entry_fill_id for t in broker.closed_trades], dtype="string"
    )
    for name in ("allocation_id", "exit_fill_id", "exit_sequence"):
        stats["_trades"][name] = pd.Series(
            [getattr(t, name) for t in broker.closed_trades],
            dtype="int64" if name == "exit_sequence" else "string",
        )
    stats["Commissions [$]"] = broker.ledger.fees_paid
    stats["# Closed Lots"] = len(
        {t.trade_id for t in broker.closed_trades} - {t.trade_id for t in broker.trades}
    )
    commission = broker._commission_model
    if isinstance(commission, Commission):
        commission = commission.snapshot()
    elif callable(commission):
        commission = {
            "reconstructable": False,
            "name": getattr(commission, "__qualname__", type(commission).__name__),
        }
        broker.diagnostics.append({"code": "commission_not_reconstructable"})
    result = type(original)(stats, dtype=object)
    result.attrs.update(original.attrs)
    result.attrs.update(
        {
            "trading_schema_version": 4,
            "execution_policy_version": "2",
            "engine_version": version("openbacktesting"),
            "instrument": asdict(broker.instrument),
            "account_model": "linear_margin",
            "execution_timing": broker.execution_timing,
            "end_policy": end_policy,
            "commission": commission,
            "spread": broker._spread,
            "slippage": asdict(broker.slippage),
            "margin": broker.margin,
            "allow_short": broker.allow_short,
            "max_gross_exposure": broker.max_gross_exposure,
            "hedging": broker._hedging,
            "diagnostics": list(broker.diagnostics),
        }
    )

    return result
