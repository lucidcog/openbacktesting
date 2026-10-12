"""Consume every report section in one run; return in-memory JSON without writing files or connecting to a webpage."""

import json
import pickle

import pandas as pd

from openbacktesting import Backtest, DataContext, Strategy, Timeframe
from openbacktesting.broker import Commission
from openbacktesting.portfolio import export_result, get_snapshot, report_catalog


class ReportStrategy(Strategy):
    """Partially exit one entry batch while retaining its balance, demonstrating signal and extrema identities."""

    def init(self):
        pass

    def next(self):
        if self.bar_index == 0:
            self.buy(qty=3, tag={"signal": "Trend entry", "comment": "Fixed offline case"})
        if self.bar_index in (1, 2):
            self.trades[0].close(qty=1)


def main():
    prices = [100.0, 112.0, 98.0, 130.0, 125.0]
    data = pd.DataFrame(
        {"Open": prices, "High": [p + 2 for p in prices], "Low": [p - 2 for p in prices], "Close": prices},
        index=pd.date_range("2026-01-01", periods=5, freq="MS", tz="UTC"),
    )
    result = Backtest(
        data,
        ReportStrategy,
        cash=1000,
        commission=Commission(per_unit=1),
        execution_timing="same_close",
        context=DataContext(Timeframe.days(1), "Asia/Shanghai"),
    ).run()
    print(result[["Return [%]", "# Trades"]])
    frozen = get_snapshot(result)
    assert pickle.loads(pickle.dumps(frozen)) == frozen
    result["_strategy"] = None  # Host consumption does not require a live strategy object.
    # Serialize the full result through its actual portfolio class path; the restored result still exports independently.
    result = pickle.loads(pickle.dumps(result))
    report = export_result(result)
    json.dumps(report, ensure_ascii=False, allow_nan=False)
    for field in report_catalog()["entries"]:
        value = report
        for segment in field["path"]:
            value = value[segment]
    closed, opened = report["trades"]["closedFragments"], report["trades"]["openLots"]
    assert len(closed) == 2 and len(opened) == 1
    assert len({t["lotId"] for t in closed}) == 1
    assert len({t["fragmentId"] for t in closed}) == 2
    assert [t["pnlNet"] for t in closed] == [10.0, -4.0]
    assert closed[0]["excursion"]["mfeMoney"] == 14
    assert opened[0]["excursion"]["mfeMoney"] == 32
    assert opened[0]["entry"]["signal"] == "Trend entry"
    assert report["summary"]["all"]["totalPnl"]["value"] == 30
    assert report["summary"]["all"]["marginCalls"]["status"] == "unsupported"
    assert report["analysis"]["periodical"]["status"] == "ok"
    assert len(report["analysis"]["periodical"]["buckets"]["monthly"]) == 5
    for name in ("breakdown", "distribution", "streaks", "timePatterns", "growthAndDecline"):
        assert report["analysis"][name]
    for name in ("account", "close", "benchmark", "directions", "margin", "closedCumulative"):
        assert report["series"][name]
    print(
        json.dumps(
            {
                "schemaVersion": report["schemaVersion"],
                "fields": len(report_catalog()["entries"]),
                "fragments": len(closed),
                "openLots": len(opened),
                "totalPnl": 30,
                "json": True,
            },
            ensure_ascii=False,
        )
    )
    return report


if __name__ == "__main__":
    main()
