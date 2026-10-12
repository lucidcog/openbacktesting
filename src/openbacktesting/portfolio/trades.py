"""订单、分配与批次的无活对象报告投影。"""

import json

import pandas as pd

from openbacktesting.portfolio.models import plain, time_ref


def signal(tag):
    if isinstance(tag, str) and tag:
        return tag, None
    if isinstance(tag, dict):
        name = tag.get("signal")
        comment = tag.get("comment")
        return (
            name if isinstance(name, str) and name else None,
            comment if isinstance(comment, str) else None,
        )
    return None, None


def excursion(state, quantity, entry_price):
    return {
        "mfeMoney": state["mfe"] * quantity,
        "maeMoney": state["mae"] * quantity,
        "mfeFraction": state["mfe"] / entry_price,
        "maeFraction": state["mae"] / entry_price,
        "mfeBar": state["mfeBar"],
        "maeBar": state["maeBar"],
        "coverage": "partial" if state["partial"] else "complete_under_bar_model",
        "methodId": "sampled_bounds_v1",
        "reason": "ambiguous_intrabar_order" if state["partial"] else None,
    }


def project_trades(stats, observations):
    facts = {
        key: stats[field].astype(object).where(stats[field].notna(), None).to_dict("records")
        for key, field in (
            ("orders", "_orders"),
            ("orderSizing", "_order_sizing"),
            ("orderEvents", "_order_events"),
            ("fills", "_fills"),
            ("allocations", "_trade_allocations"),
        )
    }
    orders = {r["order_id"]: r for r in facts["orders"]}
    fills = {r["fill_id"]: r for r in facts["fills"]}

    def leg(fill):
        tag = json.loads(orders[fill["order_id"]]["tag_json"])
        name, comment = signal(tag)
        return {
            "fillId": fill["fill_id"],
            "orderId": fill["order_id"],
            "barIndex": fill["bar_index"],
            "time": time_ref(fill["timestamp"]),
            "phase": fill["phase"],
            "sequence": fill["sequence"],
            "price": fill["price"],
            "signal": name,
            "comment": comment,
        }

    extras = {r["allocation_id"]: r for r in stats["_trades"].to_dict("records")}
    closed = []
    cumulative = 0.0
    for allocation in facts["allocations"]:
        if allocation["kind"] != "close":
            continue
        entry, exit_ = fills[allocation["entry_fill_id"]], fills[allocation["fill_id"]]
        qty = allocation["qty"]
        cost = qty * entry["price"]
        pnl = allocation["realized_pnl_gross"] - allocation["entry_fee"] - allocation["fee"]
        cumulative += pnl
        elapsed = exit_["bar_index"] - entry["bar_index"]
        duration = (
            (exit_["timestamp"] - entry["timestamp"]).value
            if isinstance(entry["timestamp"], pd.Timestamp)
            else None
        )
        closed.append(
            {
                "fragmentId": allocation["allocation_id"],
                "lotId": allocation["trade_id"],
                "displayOrdinal": len(closed) + 1,
                "direction": "long" if entry["side"] == "buy" else "short",
                "status": "closed",
                "entry": leg(entry),
                "exit": leg(exit_),
                "quantity": qty,
                "signedQuantity": qty if entry["side"] == "buy" else -qty,
                "entryNotional": cost,
                "exitNotional": qty * exit_["price"],
                "pnlGross": allocation["realized_pnl_gross"],
                "pnlNet": pnl,
                "entryFeeAllocated": allocation["entry_fee"],
                "exitFee": allocation["fee"],
                "feeTotal": allocation["entry_fee"] + allocation["fee"],
                "returnFraction": pnl / cost,
                "barsElapsed": elapsed,
                "barsHeld": elapsed + 1,
                "durationNs": str(duration) if duration is not None else None,
                "cumulativeClosedPnl": cumulative,
                "fractionOfInitialCapital": cumulative / stats.attrs["statistics_initial_equity"],
                "excursion": excursion(
                    observations.closed[allocation["allocation_id"]], qty, entry["price"]
                ),
                "extensions": plain(extras[allocation["allocation_id"]]),
            }
        )
    opened = []
    for t in stats["_open_trades"].to_dict("records"):
        entry = fills[t["entry_fill_id"]]
        opened.append(
            {
                "lotId": t["trade_id"],
                "status": "open",
                "direction": "long" if t["Size"] > 0 else "short",
                "entry": leg(entry),
                "exit": None,
                "remainingQuantity": abs(t["Size"]),
                "remainingEntryFee": t["EntryFeeRemaining"],
                "openPnlGross": t["PnLGross"],
                "openPnlNet": t["PnL"],
                "returnFraction": t["ReturnPct"],
                "markPrice": observations.rows[-1]["price"],
                "asOf": observations.rows[-1]["observationId"],
                "excursion": excursion(
                    observations.lots[t["trade_id"]], abs(t["Size"]), entry["price"]
                ),
                "tag": plain(t["Tag"]),
            }
        )
    return facts, closed, opened
