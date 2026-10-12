"""真实线程/spawn 验证上下文随优化实例传递，而非依赖全局当前图表。"""

import json
import multiprocessing as mp
import sys
from multiprocessing.pool import ThreadPool

import openbacktesting as api
import numpy as np
import pandas as pd
from openbacktesting.broker import ClosedTradeStats, Commission, InstrumentSpec
from openbacktesting.parallel import SharedMemory, SharedMemoryManager
from openbacktesting.portfolio import export_result
from openbacktesting.simulation.config import BacktestSettings
from openbacktesting.test import GOOG


class ContextStrategy(api.Strategy):
    quantity = 1

    def init(self):
        expected = {"FIRST": api.Timeframe.minutes(15), "SECOND": api.Timeframe.days(1)}
        assert self.timeframe == expected[self.instrument.symbol]
        self.observed = self.timeframe
        assert self.closed_trade_stats == ClosedTradeStats()

    def next(self):
        if len(self.data) == 2:
            for _ in range(self.quantity):
                self.buy()
        if len(self.data) == 5:
            self.close_position()

    def on_finish(self, summary):
        snapshot = self.closed_trade_stats
        assert snapshot.closed_count == self.quantity
        assert abs(snapshot.net_profit - sum(t.pl for t in self.closed_trades)) < 1e-8


def score(stats):
    expected = 0.02 if stats.attrs["instrument"]["symbol"] == "FIRST" else 0
    assert stats.attrs["statistics_risk_free_rate"] == expected
    assert stats.attrs["commission"] == Commission(per_unit=1.5).snapshot()
    report = export_result(stats)
    assert report["semantics"]["riskFreeRate"] == expected
    assert report["context"]["timezone"] == "UTC"
    return stats["Sharpe Ratio"]


def roundtrip(settings):
    assert settings.commission_type is api.CommissionType.CASH_PER_CONTRACT
    assert settings.default_qty_type is api.QuantityType.FIXED
    assert settings.slippage_type is api.SlippageType.BPS
    assert settings.execution_timing is api.ExecutionTiming.NEXT_OPEN
    assert settings.end_policy is api.EndPolicy.MARK_TO_MARKET
    return BacktestSettings.from_snapshot(json.loads(json.dumps(settings.snapshot())))


class TimezoneStrategy(api.Strategy):
    quantity = 1
    fail = False

    def init(self):
        expected = pd.to_datetime(self.df.Instant.to_numpy(), utc=True).tz_convert(
            self.instrument.symbol
        )
        pd.testing.assert_index_equal(self.data_index.as_unit("ns"), expected)
        if self.fail:
            raise ValueError("时区候选预期失败")

    def next(self):
        assert self.data_index[-1].value == self.df.Instant.iloc[-1]
        assert str(self.data_index.tz) == self.instrument.symbol
        if self.bar_index == 0:
            self.buy(qty=self.quantity)
        elif self.bar_index == 8:
            self.close_position()


def verify_timezones():
    created = []
    original = SharedMemoryManager.SharedMemory

    def record(self, **kwargs):
        segment = original(self, **kwargs)
        if kwargs.get("create"):
            created.append(segment.name)
        return segment

    SharedMemoryManager.SharedMemory = record
    cases = 0
    try:
        for start in ("2026-03-08 00:30", "2026-11-01 00:30"):
            index = pd.date_range(start, periods=48, freq="h", tz="UTC")
            prices = 100 + np.arange(len(index)) * 0.1
            data = pd.DataFrame(
                {
                    "Open": prices,
                    "High": prices + 1,
                    "Low": prices - 1,
                    "Close": prices,
                    "Instant": index.as_unit("ns").asi8,
                },
                index=index,
            )
            for zone in ("America/New_York", "Asia/Shanghai", "Asia/Kathmandu"):
                bt = api.Backtest(
                    data,
                    TimezoneStrategy,
                    context=api.DataContext(api.Timeframe.hours(1), zone),
                    instrument=InstrumentSpec(symbol=zone),
                )
                baseline = {q: bt.run(quantity=q) for q in (1, 2)}
                seen = []

                def compare(stats, baseline=baseline, seen=seen):
                    quantity = next(
                        q
                        for q in baseline
                        if stats["Equity Final [$]"] == baseline[q]["Equity Final [$]"]
                    )
                    pd.testing.assert_series_equal(stats, baseline[quantity].filter(regex="^[^_]"))
                    seen.append(quantity)
                    return stats["Equity Final [$]"]

                result, heatmap = bt.optimize(
                    quantity=[1, 2], maximize=compare, return_heatmap=True
                )
                assert sorted(seen) == [1, 2]
                for quantity in (1, 2):
                    assert heatmap.loc[(quantity,)] == baseline[quantity]["Equity Final [$]"]
                for key in ("_trades", "_fills", "_equity_curve"):
                    pd.testing.assert_frame_equal(result[key], baseline[2][key])
                assert result["_equity_curve"].index.equals(index.tz_convert(zone))
                cases += 1
        try:
            bt.optimize(quantity=[1, 2], fail=[True])
        except ValueError as error:
            assert str(error) == "时区候选预期失败"
        else:
            raise AssertionError("未传播子进程异常")
    finally:
        SharedMemoryManager.SharedMemory = original
    assert created
    for name in created:
        try:
            leaked = SharedMemory(name=name, track=False)
        except FileNotFoundError:
            continue
        leaked.close()
        raise AssertionError(f"共享内存未回收: {name}")
    return cases


def main():
    mode = sys.argv[1]
    api.Pool = (
        (lambda: mp.get_context("spawn").Pool(2)) if mode == "spawn" else (lambda: ThreadPool(2))
    )
    data = GOOG.iloc[:12].copy()
    data.index = data.index.tz_localize("UTC")
    for symbol, timeframe in (
        ("FIRST", api.Timeframe.minutes(15)),
        ("SECOND", api.Timeframe.days(1)),
    ):
        settings = BacktestSettings(
            risk_free_rate=0.02 if symbol == "FIRST" else 0,
            default_qty_value=2,
            commission_type=api.CommissionType.CASH_PER_CONTRACT,
            commission_value=1.5,
        )
        with api.Pool() as pool:
            restored = pool.apply(roundtrip, (settings,))
        assert restored == settings
        bt = api.Backtest(
            data,
            ContextStrategy,
            context=api.DataContext(timeframe, "UTC"),
            instrument=InstrumentSpec(symbol=symbol),
            **restored.kwargs(),
        )
        stats, heatmap = bt.optimize(quantity=[1, 2], maximize=score, return_heatmap=True)
        assert len(heatmap) == 2 and stats["_strategy"].observed == timeframe
        assert stats.attrs["statistics_risk_free_rate"] == (0.02 if symbol == "FIRST" else 0)
        assert stats.attrs["commission"] == Commission(per_unit=1.5).snapshot()
        assert (stats._fills.qty == 2).all() and (stats._fills.fee == 3).all()
        for quantity in (1, 2):
            direct = bt.run(quantity=quantity)
            assert heatmap.loc[(quantity,)] == score(direct)
        repeat = bt.run(quantity=stats["_strategy"].quantity)
        assert stats._fills.equals(repeat._fills)
        assert export_result(stats) == export_result(repeat)
    timezone_cases = verify_timezones()
    assert not mp.active_children()
    print(
        json.dumps({"mode": mode, "contexts": 2, "timezone_cases": timezone_cases, "children": 0})
    )


if __name__ == "__main__":
    main()
