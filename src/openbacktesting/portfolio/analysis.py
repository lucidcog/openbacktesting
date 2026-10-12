"""确定性的交易分布、连续段、时间模式与权益区间。"""

from decimal import ROUND_FLOOR, Decimal

import numpy as np
import pandas as pd

from openbacktesting.portfolio.metrics import mean
from openbacktesting.portfolio.models import metric, ratio


def distribution(trades):
    bins = {}
    for t in trades:
        key = int(
            (Decimal(str(t["returnFraction"])) / Decimal("0.01")).to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        bins.setdefault(key, []).append(t["fragmentId"])
    # 稀疏桶避免异常大收益产生巨量空桶；每桶显式边界。
    histogram = [
        {
            "lower": float(Decimal(k) * Decimal("0.01")),
            "upper": float(Decimal(k + 1) * Decimal("0.01")),
            "count": len(ids),
            "fragmentIds": ids,
        }
        for k, ids in sorted(bins.items())
    ]
    values = [t["returnFraction"] for t in trades]
    q1, q3 = np.quantile(values, [0.25, 0.75]) if len(values) >= 4 else (None, None)
    low, high = (q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)) if q1 is not None else (None, None)
    outliers = [
        t
        for t in trades
        if low is not None and (t["returnFraction"] < low or t["returnFraction"] > high)
    ]
    return {
        "histogram": histogram,
        "interval": "left_closed_right_open",
        "winners": sum(t["pnlNet"] > 0 for t in trades),
        "losers": sum(t["pnlNet"] < 0 for t in trades),
        "evens": sum(t["pnlNet"] == 0 for t in trades),
        "averageProfitReturn": mean([t["returnFraction"] for t in trades if t["pnlNet"] > 0]),
        "averageLossReturn": mean([-t["returnFraction"] for t in trades if t["pnlNet"] < 0]),
        "outliers": {
            "methodId": "tukey_return_iqr_v1",
            "lower": low,
            "upper": high,
            "fragmentIds": [t["fragmentId"] for t in outliers],
            "count": len(outliers),
            "pnl": metric(
                sum(t["pnlNet"] for t in outliers) if low is not None else None,
                "money",
                status="ok" if low is not None else "insufficient_data",
                reason="fewer_than_four_samples",
            ),
        },
    }


def streaks(trades):
    rows = []
    active = None
    for t in trades:
        sign = int(t["pnlNet"] > 0) - int(t["pnlNet"] < 0)
        if not sign:
            active = None
            continue
        if active is None or active["sign"] != sign:
            active = {
                "id": f"streak-{len(rows) + 1}",
                "sign": sign,
                "count": 0,
                "amount": 0.0,
                "startFragmentId": t["fragmentId"],
                "endFragmentId": t["fragmentId"],
                "current": False,
            }
            rows.append(active)
        active["count"] += 1
        active["amount"] += t["pnlNet"]
        active["endFragmentId"] = t["fragmentId"]
    if active is not None:
        active["current"] = True
    summary = {}
    for label, sign in (("winning", 1), ("losing", -1)):
        lengths = [r["count"] for r in rows if r["sign"] == sign]
        amounts = [abs(r["amount"]) for r in rows if r["sign"] == sign]
        summary[label] = {
            "longest": max(lengths, default=0),
            "average": mean(lengths),
            "maximumAmount": max(amounts, default=0.0),
            "averageAmount": mean(amounts),
        }
    return {"rows": rows, "summary": summary, "methodId": "zero_breaks_streak_v1"}


def time_patterns(trades, index):
    if not isinstance(index, pd.DatetimeIndex):
        return {"status": "not_applicable", "reason": "ordinal_index", "groups": {}}
    result = {}
    for name, attr, keys in (
        ("hours", "hour", range(24)),
        ("days", "dayofweek", range(7)),
        ("months", "month", range(1, 13)),
    ):
        groups = {key: [] for key in keys}
        for t in trades:
            groups[getattr(index[t["entry"]["barIndex"]], attr)].append(t)
        rows = []
        for key, group in groups.items():
            wins = sum(t["pnlNet"] > 0 for t in group)
            rows.append(
                {
                    "key": key,
                    "count": len(group),
                    "wins": wins,
                    "losses": sum(t["pnlNet"] < 0 for t in group),
                    "evens": sum(t["pnlNet"] == 0 for t in group),
                    "winRate": ratio(wins, len(group)),
                    "pnl": sum(t["pnlNet"] for t in group),
                    "averageBars": mean([t["barsHeld"] for t in group]),
                }
            )
        best = max((r["winRate"] for r in rows if r["winRate"] is not None), default=None)
        result[name] = {
            "rows": rows,
            "bestKeys": [r["key"] for r in rows if best is not None and r["winRate"] == best],
        }
    return {"status": "ok", "reason": None, "groups": result}


def episodes(rows, initial):
    if not rows:
        return {"drawdowns": [], "alternating": []}

    def duration(start, end):
        a, b = rows[start]["timestamp"], rows[end]["timestamp"]
        return str((b - a).value) if isinstance(a, pd.Timestamp) else None

    def item(start, end, kind, amount, fraction, current, extreme):
        return {
            "kind": kind,
            "start": rows[start]["observationId"],
            "end": rows[end]["observationId"],
            "extreme": rows[extreme]["observationId"],
            "amount": amount,
            "fraction": fraction,
            "durationNs": duration(start, end),
            "current": current,
            "recovered": not current,
        }

    drawdowns = []
    peak, peak_i, active, lowest, low_i = initial, 0, False, initial, 0
    for i, row in enumerate(rows):
        value = row["equity"]
        if value >= peak:
            if active:
                drawdowns.append(
                    item(
                        peak_i,
                        i,
                        "drawdown",
                        peak - lowest,
                        ratio(peak - lowest, peak),
                        False,
                        low_i,
                    )
                )
            peak, peak_i, active, lowest = value, i, False, value
        else:
            active = True
            if value < lowest:
                lowest, low_i = value, i
    if active:
        drawdowns.append(
            item(
                peak_i,
                len(rows) - 1,
                "drawdown",
                peak - lowest,
                ratio(peak - lowest, peak),
                True,
                low_i,
            )
        )
    alternating = []
    start, sign = 0, 0
    for i in range(1, len(rows)):
        delta = rows[i]["equity"] - rows[i - 1]["equity"]
        new = int(delta > 0) - int(delta < 0)
        if not new:
            continue
        if sign and new != sign:
            a, b = rows[start]["equity"], rows[i - 1]["equity"]
            alternating.append(
                item(
                    start,
                    i - 1,
                    "runup" if sign > 0 else "decline",
                    abs(b - a),
                    abs(b - a) / a if a > 0 else None,
                    False,
                    i - 1,
                )
            )
            start = i - 1
        elif not sign:
            start = i - 1
        sign = new
    if sign:
        a, b = rows[start]["equity"], rows[-1]["equity"]
        alternating.append(
            item(
                start,
                len(rows) - 1,
                "runup" if sign > 0 else "decline",
                abs(b - a),
                abs(b - a) / a if a > 0 else None,
                True,
                len(rows) - 1,
            )
        )
    summary = {}
    for name, group in (
        ("drawdown", drawdowns),
        ("growth", [r for r in alternating if r["kind"] == "runup"]),
        ("decline", [r for r in alternating if r["kind"] == "decline"]),
    ):
        summary[name] = {
            "maximum": max((r["amount"] for r in group), default=0.0),
            "average": mean([r["amount"] for r in group]),
            "maximumFraction": max(
                (r["fraction"] for r in group if r["fraction"] is not None), default=None
            ),
            "averageFraction": mean([r["fraction"] for r in group if r["fraction"] is not None]),
            "averageDurationNs": str(sum(int(r["durationNs"]) for r in group) // len(group))
            if group and all(r["durationNs"] is not None for r in group)
            else None,
            "current": next((r for r in group if r["current"]), None),
        }
    return {"drawdowns": drawdowns, "alternating": alternating, "summary": summary}
