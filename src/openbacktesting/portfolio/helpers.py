"""Existing implementation moved from lib: compute_stats."""

from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd

from openbacktesting.broker.models import finite
from openbacktesting.portfolio.rates import validate_risk_free_rate
from openbacktesting.portfolio.snapshot import refresh_snapshot
from openbacktesting.portfolio.stats import compute_stats as _compute_stats


def compute_stats(
    *,
    stats: pd.Series,
    data: pd.DataFrame,
    trades: pd.DataFrame = None,
    risk_free_rate: float = cast(float, ...),
) -> pd.Series:
    """Recompute performance statistics from existing results, data, and an optional trade subset.


    (Re-)compute strategy performance metrics.

    `stats` is the statistics series as returned by `openbacktesting.engine.Backtest.run()`.
    `data` is OHLC data as passed to the `openbacktesting.engine.Backtest`
    the `stats` were obtained in.
    `trades` can be a dataframe subset of `stats._trades` (e.g. only long trades).
    risk_free_rate is an annualized fraction used for Sharpe, Sortino, and Alpha; omission inherits the latest statistics value,
    missing records fall back to zero, explicit zero overrides, and None is invalid. Recalculation does not rewrite the original run snapshot or actual fees.
    Initial capital inherits statistics_initial_equity; historical records lacking it fall back to the first equity value.
    Initial capital must be positive and finite; approximate equity for trade subsets starts from the same principal.

        >>> stats = Backtest(GOOG, MyStrategy).run()
        >>> only_long_trades = stats._trades[stats._trades.Size > 0]
        >>> long_stats = compute_stats(stats=stats, trades=only_long_trades,
        ...                            data=GOOG, risk_free_rate=.02)
    """
    if risk_free_rate is Ellipsis:
        risk_free_rate = stats.attrs.get("statistics_risk_free_rate", 0.0)
    risk_free_rate = validate_risk_free_rate(risk_free_rate)
    equity = stats._equity_curve.Equity
    initial_equity = finite(
        stats.attrs.get("statistics_initial_equity", equity.iloc[0]),
        "initial_equity",
        positive=True,
    )
    exposure = None
    full_account = trades is None
    if full_account:
        trades = stats._trades
        if "_positions" in stats:
            positions = stats["_positions"]
            exposure = np.zeros(len(data), dtype=bool)
            bars = positions[positions.phase == "bar"]
            exposure[bars.bar_index] = bars.gross_qty > 0
    else:
        # XXX: Is this buggy?
        equity = equity.copy()
        equity[:] = initial_equity
        for t in trades.itertuples(index=False):
            equity.iloc[t.EntryBar :] += t.PnL
    result = _compute_stats(
        trades=trades,
        equity=equity.values,
        ohlc_data=data,
        risk_free_rate=risk_free_rate,
        strategy_instance=stats.get("_strategy"),
        exposure=exposure,
        initial_equity=initial_equity,
    )
    if full_account:
        preserved = {
            key: value
            for key, value in stats.items()
            if key.startswith("_")
            and key not in ("_strategy", "_trades", "_equity_curve")
            or key in ("Commissions [$]", "# Closed Lots")
        }
        result = type(result)(dict(result) | preserved, dtype=object)
    result.attrs.update(stats.attrs)
    result.attrs["statistics_risk_free_rate"] = risk_free_rate
    result.attrs["statistics_initial_equity"] = initial_equity
    if full_account:
        refresh_snapshot(result)
    else:
        result.attrs.pop("portfolio_snapshot", None)
        result.attrs["portfolio_diagnostic"] = "portfolio_unavailable_for_legacy_subset"
    return result
