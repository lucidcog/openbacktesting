"""有版本的金额、交易和路径指标；旧统计独立保留。"""

import math
from itertools import groupby

import numpy as np

from openbacktesting.portfolio.models import metric, ratio


def mean(values):
    return sum(values) / len(values) if values else None


def trade_metrics(trades, opened):
    pnl = [t["pnlNet"] for t in trades]
    wins = [t for t in trades if t["pnlNet"] > 0]
    losses = [t for t in trades if t["pnlNet"] < 0]
    gp, gl = sum(t["pnlNet"] for t in wins), -sum(t["pnlNet"] for t in losses)
    result = {}

    def put(name, value, unit="ratio", **kwargs):
        result[name] = metric(value, unit, sample=len(trades), **kwargs)

    for name, value in (
        ("closedFragmentCount", len(trades)),
        ("openLotCount", len(opened)),
        ("closedLotCount", len({t["lotId"] for t in trades} - {t["lotId"] for t in opened})),
        ("openedLotCount", len({t["lotId"] for t in trades + opened})),
        ("winningCount", len(wins)),
        ("losingCount", len(losses)),
        ("evenCount", len(trades) - len(wins) - len(losses)),
    ):
        put(name, value, "count")
    for name, value in (
        ("closedNetPnl", sum(pnl)),
        ("grossProfit", gp),
        ("grossLoss", gl),
        ("expectedPayoff", mean(pnl)),
        ("averageProfit", mean([t["pnlNet"] for t in wins])),
        ("averageLoss", mean([-t["pnlNet"] for t in losses])),
        ("closedFees", sum(t["feeTotal"] for t in trades)),
    ):
        put(name, value, "money", reason="no_closed_trades")
    put(
        "profitFactorMoney",
        ratio(gp, gl),
        reason="unbounded" if gp and not gl else "zero_denominator",
    )
    put("winRate", ratio(len(wins), len(trades)), reason="no_closed_trades")
    put("meanTradeReturn", mean([t["returnFraction"] for t in trades]), reason="no_closed_trades")
    for label, group in (("Trade", trades), ("Winning", wins), ("Losing", losses)):
        put(
            "average" + label + "Bars",
            mean([t["barsHeld"] for t in group]),
            "bars",
            reason="no_samples",
        )
    for label, group, sign in (("Profit", wins, 1), ("Loss", losses, -1)):
        put(
            "average" + label + "Return",
            mean([sign * t["returnFraction"] for t in group]),
            reason="no_samples",
        )
        for suffix, key, unit in (("", "pnlNet", "money"), ("Return", "returnFraction", "ratio")):
            item = max(group, key=lambda t: sign * t[key]) if group else None
            put(
                "largest" + label + suffix,
                sign * item[key] if item else None,
                unit,
                reference=item["fragmentId"] if item else None,
                reason="no_samples",
            )
        largest = max([sign * t["pnlNet"] for t in group], default=0.0)
        put(
            "largest" + label + "Share",
            ratio(largest, gp if sign > 0 else gl),
            reason="zero_denominator",
        )
    ap, al = mean([t["pnlNet"] for t in wins]), mean([-t["pnlNet"] for t in losses])
    put("averageProfitLossRatio", ratio(ap, al) if ap is not None else None, reason="no_samples")
    durations = [int(t["durationNs"]) for t in trades if t["durationNs"] is not None]
    put(
        "maxTradeDurationNs",
        str(max(durations)) if durations else None,
        "nanoseconds",
        reason="no_duration",
    )
    put(
        "averageTradeDurationNs",
        str(sum(durations) // len(durations)) if durations else None,
        "nanoseconds",
        reason="no_duration",
    )
    return result


def path_metrics(rows, initial, *, prefix="", approximate=False):
    high = low = initial
    max_dd = max_ru = dd_fraction = ru_fraction = 0.0
    dd_ref = ru_ref = ddf_ref = ruf_ref = None
    invalid_runup_base = False

    # 同bar未知顺序的高低点作为一组；只与此前峰谷比较，不虚构组内顺序。
    def group_key(row):
        return row["barIndex"] if not row.get("ordered", True) else row["observationId"]

    for _, group in groupby(rows, group_key):
        points = list(group)
        bottom = min(points, key=lambda r: r["equity"])
        top = max(points, key=lambda r: r["equity"])
        dd, ru = max(0.0, high - bottom["equity"]), max(0.0, top["equity"] - low)
        if dd > max_dd:
            max_dd, dd_ref = dd, bottom["observationId"]
        if ru > max_ru:
            max_ru, ru_ref = ru, top["observationId"]
        if high > 0 and dd / high > dd_fraction:
            dd_fraction, ddf_ref = dd / high, bottom["observationId"]
        if ru > 0 and low <= 0:
            invalid_runup_base = True
        if low > 0 and ru / low > ru_fraction:
            ru_fraction, ruf_ref = ru / low, top["observationId"]
        high, low = max(high, top["equity"]), min(low, bottom["equity"])
    result = {}
    for key, value, unit, ref in (
        ("maxDrawdown", max_dd, "money", dd_ref),
        ("maxRunup", max_ru, "money", ru_ref),
        ("maxDrawdownFraction", dd_fraction, "ratio", ddf_ref),
        ("maxRunupFraction", None if invalid_runup_base else ru_fraction, "ratio", ruf_ref),
        ("maxDrawdownInitialFraction", max_dd / initial, "ratio", dd_ref),
        ("maxRunupInitialFraction", max_ru / initial, "ratio", ru_ref),
    ):
        result[prefix + key] = metric(
            value,
            unit,
            reference=ref,
            method="sampled_bounds_v1" if approximate else "close_path_v1",
            status="undefined" if value is None else ("approximate" if approximate else "ok"),
            reason="nonpositive_runup_base"
            if value is None
            else ("unknown_intrabar_order" if approximate else None),
        )
    return result


def monthly_risk(periods, rf):
    returns = [p["equityReturn"] for p in periods]
    if len(returns) < 2 or any(r is None for r in returns):
        return {
            k: metric(
                None,
                method="monthly_compounded_rf_v1",
                status="insufficient_data",
                reason="invalid_or_insufficient_periods",
                sample=len(returns),
            )
            for k in ("sharpe", "sortino")
        }
    excess = np.asarray(returns) - ((1 + rf) ** (1 / 12) - 1)
    denominators = (float(np.std(returns)), float(np.sqrt(np.mean(np.minimum(excess, 0) ** 2))))
    return {
        k: metric(
            ratio(float(np.mean(excess)) * math.sqrt(12), d),
            method="monthly_compounded_rf_v1",
            reason="zero_denominator",
            sample=len(returns),
        )
        for k, d in zip(("sharpe", "sortino"), denominators)
    }


def correlation(x, y):
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 2:
        return metric(
            None,
            status="insufficient_data",
            reason="insufficient_pairs",
            sample=len(pairs),
            method="paired_period_returns_v1",
        )
    a, b = np.array(pairs).T
    value = float(np.corrcoef(a, b)[0, 1]) if np.std(a) and np.std(b) else None
    return metric(
        value, reason="zero_variance", sample=len(pairs), method="paired_period_returns_v1"
    )
