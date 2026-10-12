"""从 lib 迁入的既有实现：compute_stats。"""

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
    """从既有结果、数据及可选交易子集重新计算绩效统计。


    (Re-)compute strategy performance metrics.

    `stats` is the statistics series as returned by `openbacktesting.engine.Backtest.run()`.
    `data` is OHLC data as passed to the `openbacktesting.engine.Backtest`
    the `stats` were obtained in.
    `trades` can be a dataframe subset of `stats._trades` (e.g. only long trades).
    risk_free_rate 为年化小数，用于 Sharpe、Sortino 与 Alpha；省略时继承最近统计值，
    缺失记录回退零，显式零覆盖，None 无效。重算不改写原运行快照或实际费用。
    初始资金继承 statistics_initial_equity；历史缺失记录回退首条权益。
    初始资金必须为正数有限值，交易子集的近似权益也从该本金开始。

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
