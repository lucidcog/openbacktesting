"""Freeze complete facts at runtime; derive reports on reads without executing user code."""

import json

import pandas as pd

from openbacktesting.portfolio.builder import build_report, legacy
from openbacktesting.portfolio.models import plain, time_ref
from openbacktesting.portfolio.trades import project_trades


class PortfolioSnapshot(str):
    """Immutable versioned fact text; read complete reports through to_dict.

    Snapshots hold no strategy, pandas objects, or mutable inputs. Derived analyses read only frozen facts;
    the text itself is an internal storage format; cross-language consumers use export_result reports.
    """

    __slots__ = ()

    def __new__(cls, payload: str):
        return super().__new__(cls, payload)

    def to_dict(self) -> dict:
        """Compute and return an independent strict JSON report without modifying the snapshot or executing strategies."""
        return plain(build_report(json.loads(self)))


def freeze(payload):
    return PortfolioSnapshot(
        json.dumps(
            payload, default=plain, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
    )


def capture_snapshot(stats, data, observations, reason, context=None):
    facts, closed, opened = project_trades(stats, observations)
    columns = list(observations.rows[0])
    keys = (
        "statistics_initial_equity",
        "statistics_risk_free_rate",
        "instrument",
        "execution_policy_version",
        "trading_schema_version",
        "engine_version",
        "commission",
        "spread",
        "slippage",
        "margin",
        "end_policy",
        "execution_timing",
        "hedging",
        "allow_short",
        "max_gross_exposure",
        "diagnostics",
    )
    attrs = {k: plain(stats.attrs[k]) for k in keys}
    attrs.update({k: plain(stats.attrs.get(k)) for k in ("input_snapshot", "backtest_snapshot")})
    return freeze(
        {
            "format": "openbacktesting_portfolio_facts_v1",
            "facts": facts,
            "closed": closed,
            "opened": opened,
            "columns": columns,
            "rows": [list(r.values()) for r in observations.rows],
            "index": data.index.as_unit("ns").asi8.astype(str).tolist()
            if isinstance(data.index, pd.DatetimeIndex)
            else data.index.tolist(),
            "close": data.Close.tolist(),
            "high": data.High.tolist(),
            "low": data.Low.tolist(),
            "timeKind": time_ref(data.index[0])["kind"],
            "timezone": str(data.index.tz)
            if isinstance(data.index, pd.DatetimeIndex) and data.index.tz
            else None,
            "reason": reason,
            "context": plain(context),
            "attrs": attrs,
            "legacy": legacy(stats),
        }
    )


def refresh_snapshot(result):
    snapshot = result.attrs.get("portfolio_snapshot")
    if snapshot is None:
        return
    source = json.loads(snapshot)
    source["attrs"]["statistics_risk_free_rate"] = result.attrs["statistics_risk_free_rate"]
    source["attrs"]["backtest_snapshot"] = plain(result.attrs.get("backtest_snapshot"))
    source["legacy"] = legacy(result)
    result.attrs["portfolio_snapshot"] = freeze(source)


def get_snapshot(result: pd.Series) -> PortfolioSnapshot:
    """Read the frozen fact snapshot; explicitly reject old results or trade subsets lacking complete facts.

    Raises:
        ValueError: The result did not collect Portfolio data.
    """
    snapshot = result.attrs.get("portfolio_snapshot")
    if not isinstance(snapshot, PortfolioSnapshot):
        raise ValueError("portfolio_snapshot_missing")  # noqa: TRY004 — missing snapshot rather than incorrect argument type
    return snapshot


def export_result(result: pd.Series) -> dict:
    """Return an independent plain-value copy of the complete report without file, network, or plotting side effects."""
    return get_snapshot(result).to_dict()
