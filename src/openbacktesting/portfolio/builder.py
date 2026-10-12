"""Assemble Portfolio once; project trade facts only after simulation ends."""

import math
from types import SimpleNamespace

import pandas as pd

from openbacktesting.portfolio.analysis import distribution, episodes, streaks, time_patterns
from openbacktesting.portfolio.metrics import mean, monthly_risk, path_metrics, trade_metrics
from openbacktesting.portfolio.models import metric, ratio, time_ref
from openbacktesting.portfolio.periods import benchmarks, periodical


def contributions(rows, facts, initial):
    fills = {f["fill_id"]: f for f in facts["fills"]}
    grouped = {}
    for a in facts["allocations"]:
        f = fills[a["fill_id"]]
        side = "long" if fills[a["entry_fill_id"]]["side"] == "buy" else "short"
        grouped.setdefault(f["sequence"], []).append((side, a["realized_pnl_gross"] - a["fee"]))
    pending = iter(sorted(grouped.items()))
    current = next(pending, None)
    balance = {"long": 0.0, "short": 0.0}
    result = {"long": [], "short": []}
    for row in rows:
        while current is not None and current[0] <= row["fillSequence"]:
            for side, value in current[1]:
                balance[side] += value
            current = next(pending, None)
        for side, sign in (("long", 1), ("short", -1)):
            qty = row[side + "_qty"]
            avg = row[side + "_avg_price"]
            unrealized = sign * qty * (row["price"] - avg) if avg is not None else 0.0
            result[side].append(
                {
                    "observationId": row["observationId"],
                    "barIndex": row["barIndex"],
                    "timestamp": row["timestamp"],
                    "phase": row["phase"],
                    "contribution": balance[side] + unrealized,
                    "equity": initial + balance[side] + unrealized,
                }
            )
    return result


def legacy(stats):
    return {
        str(k): metric(v, "native", method="engine_legacy_v1")
        for k, v in stats.items()
        if not k.startswith("_")
    }


def build_report(source):
    stats = SimpleNamespace(attrs=source["attrs"])
    kind, timezone = source["timeKind"], source["timezone"]
    if kind == "ordinal":
        index = pd.Index(source["index"])
    else:
        index = pd.to_datetime([int(t) for t in source["index"]], utc=kind == "aware")
        if timezone:
            index = index.tz_convert(timezone)
    data = pd.DataFrame({"Close": source["close"]}, index=index)
    initial = stats.attrs["statistics_initial_equity"]
    facts, closed, opened = source["facts"], source["closed"], source["opened"]
    rows = [dict(zip(source["columns"], row)) for row in source["rows"]]
    expanded, id_map = [], {}
    for row in rows:
        row["timestamp"] = index[row["barIndex"]]
        eligible = row.pop("rangeEligible")
        if eligible:
            for price in (source["high"][row["barIndex"]], source["low"][row["barIndex"]]):
                extreme = row.copy()
                gross = row["unrealized_pnl_gross"] + row["net_qty"] * (price - row["price"])
                equity = row["balance"] + gross
                used = row["gross_qty"] * price * stats.attrs["margin"]
                cost = sum(
                    row[side + "_qty"] * (row[side + "_avg_price"] or 0)
                    for side in ("long", "short")
                )
                extreme.update(
                    price=price,
                    phase="bar_range",
                    ordered=False,
                    equity=equity,
                    unrealized_pnl_gross=gross,
                    unrealized_pnl_net=gross - row["entry_fees_remaining"],
                    margin_used=used,
                    margin_available=max(0.0, equity - used),
                    gross_notional=row["gross_qty"] * price,
                    net_notional=row["net_qty"] * price,
                    return_fraction=(gross - row["entry_fees_remaining"]) / cost
                    if cost and row["avg_price"] is not None
                    else None,
                )
                expanded.append(extreme)
        old_id = row["observationId"]
        expanded.append(row)
        id_map[old_id] = f"observation-{len(expanded)}"
    rows = expanded
    for i, row in enumerate(rows, 1):
        row.update(observationId=f"observation-{i}", observationSequence=i)
    for lot in opened:
        lot["asOf"] = id_map[lot["asOf"]]
    for table in (facts["fills"], facts["orderEvents"]):
        for row in table:
            row["timestamp"] = index[row["bar_index"]]
    reason, context = source["reason"], source["context"]
    # Snapshot curves retain each bar's final ordinary close and a separate terminal snapshot; intermediate observations in the same close phase do not overwrite them.
    bar_rows = {r["barIndex"]: r for r in rows if r["phase"] == "bar"}
    close_rows = [bar_rows[i] for i in sorted(bar_rows)] + [
        r for r in rows if r["phase"] == "terminal"
    ]
    end = rows[-1]["barIndex"]
    benchmark = benchmarks(
        data, rows, facts["fills"], facts["allocations"], stats.attrs["instrument"], initial
    )
    periods = periodical(
        rows, closed, facts["fills"], benchmark["input_start_close"], initial, data.index
    )
    direction = contributions(rows, facts, initial)
    summary = {}
    directional_monthly = {}
    close_ids = {v["observationId"] for v in close_rows}
    for side in ("all", "long", "short"):
        trades = [t for t in closed if side == "all" or t["direction"] == side]
        lots = [t for t in opened if side == "all" or t["direction"] == side]
        values = trade_metrics(trades, lots)
        path = (
            close_rows
            if side == "all"
            else [r for r in direction[side] if r["observationId"] in close_ids]
        )
        values.update(path_metrics(path, initial))
        final = path[-1]["equity"]
        for key, val, unit in (
            ("initialCapital", initial, "money"),
            ("equityFinal", final, "money"),
            ("equityPeak", max([initial] + [r["equity"] for r in path]), "money"),
            ("totalPnl", final - initial, "money"),
            ("totalReturn", (final - initial) / initial, "ratio"),
            ("openPnlGross", sum(t["openPnlGross"] for t in lots), "money"),
            ("openPnlNet", sum(t["openPnlNet"] for t in lots), "money"),
            ("remainingEntryFees", sum(t["remainingEntryFee"] for t in lots), "money"),
            (
                "feesPaid",
                sum(t["feeTotal"] for t in trades) + sum(t["remainingEntryFee"] for t in lots),
                "money",
            ),
            ("closedPnlGross", sum(t["pnlGross"] for t in trades), "money"),
            (
                "totalPnlGross",
                sum(t["pnlGross"] for t in trades) + sum(t["openPnlGross"] for t in lots),
                "money",
            ),
            ("closedReturn", sum(t["pnlNet"] for t in trades) / initial, "ratio"),
        ):
            values[key] = metric(
                val,
                unit,
                method="shared_initial_capital_v1" if side != "all" else "openbacktesting_portfolio_v1",
            )
        if side != "all":
            monthly = []
            if isinstance(data.index, pd.DatetimeIndex):
                endpoints = {}
                for row in path:
                    endpoints[data.index[row["barIndex"]].strftime("%Y-%m")] = row["equity"]
                previous = initial
                for key in periods["buckets"].get("monthly", []):
                    stamp = pd.Timestamp(int(key["start"]["value"]), tz="UTC")
                    if data.index.tz:
                        stamp = stamp.tz_convert(data.index.tz)
                    value = endpoints.get(stamp.strftime("%Y-%m"), previous)
                    monthly.append({"equityReturn": value / previous - 1 if previous > 0 else None})
                    previous = value
            values.update(monthly_risk(monthly, stats.attrs["statistics_risk_free_rate"]))
            directional_monthly[side] = monthly
        summary[side] = values
    all_ = summary["all"]
    last = rows[-1]
    all_["balance"] = metric(last["balance"], "money")
    all_["feesPaid"] = metric(last["fees_paid"], "money")
    all_["commissionLoad"] = metric(
        ratio(last["fees_paid"], sum(abs(f["qty"] * f["price"]) for f in facts["fills"])),
        method="commission_load_gross_activity_v1",
        reason="zero_denominator",
    )
    average_margin = mean([r["margin_used"] for r in bar_rows.values()])
    all_["averageMarginUsed"] = metric(average_margin, "money", method="bar_close_mean_v1")
    all_["maxMarginUsed"] = metric(
        max(r["margin_used"] for r in rows), "money", method="execution_samples_v1"
    )
    for key, field in (
        ("maxGrossQuantity", "gross_qty"),
        ("maxLongQuantity", "long_qty"),
        ("maxShortQuantity", "short_qty"),
        ("maxNetQuantity", "net_qty"),
    ):
        all_[key] = metric(
            max(abs(r[field]) for r in rows), "quantity", method="execution_samples_v1"
        )
    all_.update(path_metrics(rows, initial, prefix="intrabar.", approximate=True))
    required = max(0.0, max(r["margin_used"] - (r["equity"] - initial) for r in rows))
    all_["observedCapitalRequired"] = metric(
        required, "money", method="observed_capital_requirement_v1"
    )
    net = all_["closedNetPnl"]["value"]
    for key, denominator in (
        ("returnOnInitialCapital", initial),
        ("returnOnMaxDrawdown", all_["intrabar.maxDrawdown"]["value"]),
        ("netPnlToLargestLoss", all_["largestLoss"]["value"]),
        ("marginEfficiency", average_margin),
        ("returnOnObservedCapital", required),
    ):
        all_[key] = metric(
            ratio(net, denominator),
            method="observed_capital_efficiency_v1",
            reason="zero_denominator",
        )
    for key in (
        "marginCalls",
        "totalMarginLiquidatedVolume",
        "largestMarginLiquidatedVolume",
        "tvAccountSizeRequired",
        "tvReturnOnAccountSize",
        "currencyConversion",
        "contractMultiplier",
    ):
        all_[key] = metric(
            None,
            "count" if key == "marginCalls" else "money",
            status="unsupported",
            reason="unsupported_trading_model",
        )
    all_.update(
        monthly_risk(
            periods["buckets"].get("monthly", []), stats.attrs["statistics_risk_free_rate"]
        )
    )
    years = (
        (data.index[end] - data.index[0]).total_seconds() / (365.25 * 86400)
        if isinstance(data.index, pd.DatetimeIndex)
        else 0.0
    )
    exponent = math.log(last["equity"] / initial) / years if years and last["equity"] > 0 else None
    cagr = math.expm1(exponent) if exponent is not None and exponent < 709 else None
    all_["cagr"] = metric(cagr, reason="nonpositive_equity_or_duration")
    all_["buyHoldPnl"] = metric(benchmark["input_start_close"]["points"][-1]["pnlMoney"], "money")
    all_["buyHoldReturn"] = metric(benchmark["input_start_close"]["points"][-1]["returnFraction"])
    all_["outperformance"] = metric(benchmark["input_start_close"]["points"][-1]["outperformance"])
    all_["correlation"] = periods["correlations"].get(
        "daily", metric(None, status="not_applicable", reason="ordinal_index")
    )
    breakdown = {}
    for grouping in ("signal", "direction"):
        groups = {}
        for t in closed:
            key = t["entry"]["signal"] if grouping == "signal" else t["direction"]
            groups.setdefault(key, []).append(t)
        for t in opened:
            key = t["entry"]["signal"] if grouping == "signal" else t["direction"]
            groups.setdefault(key, [])
        breakdown[grouping] = [
            {
                "key": key,
                "metrics": trade_metrics(
                    group,
                    [
                        t
                        for t in opened
                        if (t["entry"]["signal"] if grouping == "signal" else t["direction"]) == key
                    ],
                ),
                "openPnlNet": sum(
                    t["openPnlNet"]
                    for t in opened
                    if (t["entry"]["signal"] if grouping == "signal" else t["direction"]) == key
                ),
            }
            for key, group in groups.items()
        ]
    terminal = {}
    for why in ("insolvent", "end_liquidation"):
        terminal[why] = {
            "quantity": sum(f["qty"] for f in facts["fills"] if f["reason"] == why),
            "notional": sum(f["qty"] * f["price"] for f in facts["fills"] if f["reason"] == why),
        }
    payload = {
        "schemaVersion": "1.0.0",
        "semantics": {
            "metricsDefinitionVersion": "openbacktesting_portfolio_v1",
            "executionPolicyVersion": stats.attrs["execution_policy_version"],
            "tradingSchemaVersion": stats.attrs["trading_schema_version"],
            "engineVersion": stats.attrs["engine_version"],
            "tradingViewCompatibility": "not_verified",
            "riskFreeRate": stats.attrs["statistics_risk_free_rate"],
        },
        "run": {
            "runId": None,
            "strategyRef": None,
            "datasetRef": None,
            "inputRange": [time_ref(data.index[0]), time_ref(data.index[-1])],
            "executedRange": [time_ref(data.index[0]), time_ref(data.index[end])],
            "processedThroughBar": end,
            "terminationReason": reason,
            "complete": reason == "end_of_data",
        },
        "context": {
            "instrument": stats.attrs["instrument"],
            "timezone": str(data.index.tz)
            if isinstance(data.index, pd.DatetimeIndex) and data.index.tz
            else None,
            "timeKind": time_ref(data.index[0])["kind"],
            "dataContext": context,
            "settings": {
                k: stats.attrs[k]
                for k in (
                    "commission",
                    "spread",
                    "slippage",
                    "margin",
                    "end_policy",
                    "execution_timing",
                    "hedging",
                    "allow_short",
                    "max_gross_exposure",
                )
            },
            "inputs": stats.attrs.get("input_snapshot"),
            "backtest": stats.attrs.get("backtest_snapshot"),
        },
        "facts": facts,
        "trades": {"closedFragments": closed, "openLots": opened},
        "summary": summary,
        "series": {
            "account": rows,
            "close": close_rows,
            "directions": direction,
            "benchmark": benchmark,
            "closedCumulative": [
                {
                    "fragmentId": t["fragmentId"],
                    "value": t["cumulativeClosedPnl"],
                    "fraction": t["fractionOfInitialCapital"],
                }
                for t in closed
            ],
            "margin": [
                {
                    "observationId": r["observationId"],
                    "margin": r["margin_used"],
                    "utilization": r["margin_used"] / r["equity"] if r["equity"] > 0 else None,
                }
                for r in rows
            ],
        },
        "analysis": {
            "directionalMonthly": directional_monthly,
            "breakdown": breakdown,
            "periodical": periods,
            "distribution": distribution(closed),
            "streaks": streaks(closed),
            "timePatterns": time_patterns(closed, data.index),
            "growthAndDecline": episodes(close_rows, initial),
            "liquidations": terminal,
        },
        "extensions": {"legacy": source["legacy"]},
        "diagnostics": list(stats.attrs["diagnostics"]),
    }
    for table in facts.values():
        for row in table:
            if "timestamp" in row:
                row["timestamp"] = time_ref(row["timestamp"])
    for row in rows:
        row["timestamp"] = time_ref(row["timestamp"])
    for curve in direction.values():
        for row in curve:
            row["timestamp"] = time_ref(row["timestamp"])
    return payload
