"""Chart-calendar buckets, benchmarks, and period correlations."""

from decimal import ROUND_FLOOR, Decimal

import pandas as pd

from openbacktesting.portfolio.metrics import correlation
from openbacktesting.portfolio.models import time_ref


def benchmarks(data, rows, fills, allocations, instrument, initial):
    close_prices = data.Close.to_numpy()
    first = next((a for a in allocations if a["kind"] == "open"), None)
    by_id = {f["fill_id"]: f for f in fills}
    configs = [("input_start_close", 0, float(data.Close.iloc[0]), initial)]
    if first:
        fill = by_id[first["fill_id"]]
        before = next(
            r
            for r in rows
            if r["phase"].startswith("before_")
            and r["fillSequence"] < fill["sequence"]
            and r["barIndex"] == fill["bar_index"]
        )
        configs.append(("first_entry_price", fill["bar_index"], fill["price"], before["equity"]))
    result = {}
    for name, start, price, base in configs:
        step = Decimal(str(instrument["quantity_step"]))
        qty = float(
            (Decimal(str(initial)) / Decimal(str(price)) / step).to_integral_value(
                rounding=ROUND_FLOOR
            )
            * step
        )
        if qty < instrument["min_quantity"] or qty * price < instrument["min_notional"]:
            qty = 0.0
        cash = initial - qty * price
        points = []
        for r in rows:
            if r["phase"] not in ("bar", "terminal") or r["barIndex"] < start:
                continue
            equity = cash + qty * float(close_prices[r["barIndex"]])
            strategy = initial + r["equity"] - base
            points.append(
                {
                    "observationId": r["observationId"],
                    "barIndex": r["barIndex"],
                    "equity": equity,
                    "pnlMoney": equity - initial,
                    "returnFraction": (equity - initial) / initial,
                    "strategyReturn": (strategy - initial) / initial,
                    "outperformance": (strategy - equity) / initial,
                    "outperformanceMoney": strategy - equity,
                }
            )
        result[name] = {
            "status": "ok",
            "quantity": qty,
            "cash": cash,
            "entryPrice": price,
            "startBar": start,
            "costPolicy": "none",
            "points": points,
            "summary": {
                key: {
                    "minimum": min(p[key] for p in points),
                    "maximum": max(p[key] for p in points),
                    "current": points[-1][key],
                }
                for key in (
                    "returnFraction",
                    "strategyReturn",
                    "outperformance",
                    "outperformanceMoney",
                )
            },
        }
    if not first:
        result["first_entry_price"] = {
            "status": "not_applicable",
            "reason": "no_entry",
            "points": [],
        }
    return result


def periodical(rows, trades, fills, benchmark, initial, index):
    if not isinstance(index, pd.DatetimeIndex):
        return {
            "status": "not_applicable",
            "reason": "ordinal_index",
            "buckets": {},
            "correlations": {},
        }
    result, correlations = {}, {}
    start, end = index[0], index[max(r["barIndex"] for r in rows)]
    timezone = index.tz
    naive = index.tz_localize(None) if timezone else index
    for label, freq in (
        ("daily", "D"),
        ("weekly", "W-SUN"),
        ("monthly", "M"),
        ("quarterly", "Q"),
        ("yearly", "Y"),
    ):
        keys = list(naive.to_period(freq))
        covered = pd.period_range(keys[0], keys[max(r["barIndex"] for r in rows)], freq=freq)
        groups = {key: [] for key in covered}
        closed = {key: [] for key in covered}
        paid = {key: 0.0 for key in covered}
        for row in rows:
            groups[keys[row["barIndex"]]].append(row)
        for t in trades:
            closed[keys[t["exit"]["barIndex"]]].append(t)
        for f in fills:
            paid[keys[f["bar_index"]]] += f["fee"]
        previous, previous_bench = initial, initial
        bench_by_bar = {p["barIndex"]: p["equity"] for p in benchmark["points"]}
        buckets = []
        for key, group in groups.items():
            last = group[-1]["equity"] if group else previous
            # Carry forward only unobserved buckets within the calendar range; never extend the execution range.
            bvalue = bench_by_bar[group[-1]["barIndex"]] if group else previous_bench
            left, right = key.start_time, (key + 1).start_time
            if timezone:
                left = left.tz_localize(timezone, ambiguous=True, nonexistent="shift_forward")
                right = right.tz_localize(timezone, ambiguous=True, nonexistent="shift_forward")
            ts = closed[key]
            values = [r["equity"] for r in group]
            buckets.append(
                {
                    "start": time_ref(left),
                    "endExclusive": time_ref(right),
                    "partial": left < start or right > end,
                    "carriedForward": not group,
                    "count": len(group),
                    "firstBar": group[0]["barIndex"] if group else None,
                    "lastBar": group[-1]["barIndex"] if group else None,
                    "closedNetPnl": sum(t["pnlNet"] for t in ts),
                    "grossProfit": sum(max(0, t["pnlNet"]) for t in ts),
                    "grossLoss": sum(max(0, -t["pnlNet"]) for t in ts),
                    "closedFees": sum(t["feeTotal"] for t in ts),
                    "fees": paid[key],
                    "equityReturn": last / previous - 1 if previous > 0 else None,
                    "benchmarkReturn": bvalue / previous_bench - 1 if previous_bench > 0 else None,
                    "favorableExcursion": max([0.0] + [v - previous for v in values]),
                    "adverseExcursion": max([0.0] + [previous - v for v in values]),
                    "coverage": "partial"
                    if any(r["coverage"] == "partial" for r in group)
                    else "complete_under_bar_model",
                }
            )
            previous, previous_bench = last, bvalue
        for b in buckets:
            b["outperformance"] = (
                b["equityReturn"] - b["benchmarkReturn"]
                if b["equityReturn"] is not None and b["benchmarkReturn"] is not None
                else None
            )
        result[label] = buckets
        correlations[label] = correlation(
            [b["equityReturn"] for b in buckets], [b["benchmarkReturn"] for b in buckets]
        )
    return {"status": "ok", "reason": None, "buckets": result, "correlations": correlations}
