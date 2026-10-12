"""运行时冻结完整事实；读取时派生报告，不执行用户代码。"""

import json

import pandas as pd

from openbacktesting.portfolio.builder import build_report, legacy
from openbacktesting.portfolio.models import plain, time_ref
from openbacktesting.portfolio.trades import project_trades


class PortfolioSnapshot(str):
    """不可变的版本化事实文本；通过to_dict读取完整报告。

    快照不持有策略、pandas或可变输入。派生分析只读取已冻结事实；
    文本自身是内部存储格式，跨语言消费使用export_result的报告。
    """

    __slots__ = ()

    def __new__(cls, payload: str):
        return super().__new__(cls, payload)

    def to_dict(self) -> dict:
        """计算并返回独立的严格JSON报告；不修改快照或执行策略。"""
        return build_report(json.loads(self))


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
    """读取冻结事实快照；旧结果或交易子集缺少完整事实时明确拒绝。

    Raises:
        ValueError: 结果未采集Portfolio。
    """
    snapshot = result.attrs.get("portfolio_snapshot")
    if not isinstance(snapshot, PortfolioSnapshot):
        raise ValueError("portfolio_snapshot_missing")  # noqa: TRY004 — 缺少快照而非参数类型错误
    return snapshot


def export_result(result: pd.Series) -> dict:
    """返回完整报告的独立纯值副本；无文件、网络和绘图副作用。"""
    return get_snapshot(result).to_dict()
