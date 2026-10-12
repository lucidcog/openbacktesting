"""Independent regressions for chart day boundaries, absolute times, and shared-memory DST fidelity."""

from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from openbacktesting import DataContext, EndPolicy, RunLogs, Strategy, Timeframe, backtest, runtime
from openbacktesting.broker import InstrumentSpec
from openbacktesting.parallel import SharedMemoryManager
from openbacktesting.plotting import export_result


def candles(index, prices=None):
    prices = np.arange(len(index), dtype=float) + 100 if prices is None else prices
    return pd.DataFrame(
        {"Open": prices, "High": prices + 1, "Low": prices - 1, "Close": prices}, index=index
    )


@pytest.mark.parametrize("unit", ["s", "ms", "us", "ns"])
@pytest.mark.parametrize(
    "times,zone",
    [
        (["2026-11-01T05:30Z", "2026-11-01T06:30Z"], "America/New_York"),
        (["2026-11-01T06:30Z"], "America/New_York"),
        (["2026-03-08T06:30Z", "2026-03-08T07:30Z"], "America/New_York"),
        (["2026-01-05T01:00Z", "2026-01-05T02:00Z"], "Asia/Kathmandu"),
    ],
)
def test_shared_timezone_roundtrip_preserves_instants_columns_and_units(times, zone, unit):
    index = pd.to_datetime(times, utc=True).as_unit(unit)
    index += pd.Timedelta(123, unit=unit)
    index = index.tz_convert(zone)
    data = candles(index)
    data["observed_at"] = index.tz_convert("Asia/Shanghai")
    data.loc[data.index[-1], "observed_at"] = pd.NaT
    original = data.copy(deep=True)
    with SharedMemoryManager() as manager:
        restored, handles = manager.shm2df(manager.df2shm(data))
        try:
            pd.testing.assert_frame_equal(restored, original)
            saved_index = restored.index
            copied = restored.copy(deep=True)
            del restored
        finally:
            for handle in handles:
                handle.close()
    pd.testing.assert_frame_equal(copied, original)
    assert saved_index.equals(index)
    assert saved_index.dtype == index.dtype
    np.testing.assert_array_equal(saved_index.asi8, index.asi8)
    pd.testing.assert_frame_equal(data, original)


@pytest.mark.parametrize(
    "index",
    [
        pd.RangeIndex(3),
        pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-04"]),
        pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-04"], utc=True),
    ],
)
def test_shared_timezone_compatible_plain_values(index):
    data = candles(index)
    data["naive"] = pd.date_range("2026-01-01", periods=3).as_unit("ms")
    with SharedMemoryManager() as manager:
        restored, handles = manager.shm2df(manager.df2shm(data))
        try:
            pd.testing.assert_frame_equal(restored, data)
            copied = restored.copy(deep=True)
            del restored
        finally:
            for handle in handles:
                handle.close()
    pd.testing.assert_frame_equal(copied, data)


@backtest()
class TimedTrade(Strategy):
    def init(self):
        self.observed = []

    def next(self):
        self.observed.append(self.data_index[-1])
        self.log.info("Current bar")
        if self.bar_index == 0:
            self.buy(qty=1)
        elif self.bar_index == 2:
            self.close_position()


def execute(strategy, data, zone, **kwargs):
    return runtime.run(
        {"__name__": strategy.__module__, "strategy": strategy},
        data=data,
        context=DataContext(Timeframe.hours(1), zone),
        instrument=InstrumentSpec(symbol="CLOCK"),
        **kwargs,
    )


def test_timezone_output_identifies_dst_bars_without_changing_system_clock():
    data = candles(pd.date_range("2026-11-01 04:30", periods=5, freq="h", tz="UTC"))
    logs = RunLogs()
    result = execute(TimedTrade, data, "America/New_York", logs=logs)
    local = data.index.tz_convert("America/New_York")
    assert [time.isoformat() for time in local[1:3]] == [
        "2026-11-01T01:30:00-04:00",
        "2026-11-01T01:30:00-05:00",
    ]
    assert result["_equity_curve"].index.equals(local)
    assert result["_strategy"].observed == list(local)
    records = logs.get_logs()
    assert [entry["bar_time"] for entry in records] == [time.isoformat() for time in local]
    assert all(datetime.fromisoformat(entry["recorded_at"]).tzinfo == UTC for entry in records)
    trade = result["_trades"].iloc[0]
    assert trade.EntryTime == local[1] and trade.ExitTime == local[3]
    assert str(trade.EntryTime.tz) == str(trade.ExitTime.tz) == "America/New_York"
    snapshot = result.attrs["backtest_snapshot"]
    assert snapshot["schemaVersion"] == 2
    assert snapshot["context"]["timezone"] == "America/New_York"
    payload = export_result(result)
    assert payload["schemaVersion"] == "1.1.0"
    assert payload["axes"][0]["labels"] == [str(time.value) for time in data.index]
    assert payload["axes"][0]["timezone"] == "America/New_York"


@backtest(cash=1000, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class Hold(Strategy):
    def init(self):
        pass

    def next(self):
        if self.bar_index == 0:
            self.buy(qty=1)


def test_statistics_use_chart_days_with_independent_bucket_expectations():
    data = candles(
        pd.to_datetime(
            [
                "2026-01-05T14:00Z",
                "2026-01-05T17:00Z",
                "2026-01-05T23:00Z",
                "2026-01-06T01:00Z",
                "2026-01-06T16:00Z",
                "2026-01-07T02:00Z",
            ]
        ),
        np.array([100.0, 100.0, 110.0, 120.0, 115.0, 125.0]),
    )
    results = []
    # Manual groups: UTC [14,17,23] / [01,16] / [02]; Shanghai [22] / [01,07,09] / [00,10].
    for zone, ends in [
        ("UTC", [1010.0, 1015.0, 1025.0]),
        ("Asia/Shanghai", [1000.0, 1020.0, 1025.0]),
    ]:
        result = execute(Hold, data, zone)
        equity = result["_equity_curve"].Equity
        np.testing.assert_array_equal(equity, [1000.0, 1000.0, 1010.0, 1020.0, 1015.0, 1025.0])
        np.testing.assert_array_equal(equity.resample("D").last(), ends)
        returns = np.array(ends) / np.array([1000.0, *ends[:-1]]) - 1
        growth = (1025 / 1000) ** (1 / 3)
        annual = growth**252 - 1  # Both chart timezones span Monday through Wednesday.
        volatility = np.sqrt((returns.var(ddof=1) + growth**2) ** 252 - growth**504)
        assert result["Return (Ann.) [%]"] == pytest.approx(annual * 100)
        assert result["Volatility (Ann.) [%]"] == pytest.approx(volatility * 100)
        assert result["Sharpe Ratio"] == pytest.approx(annual / volatility)
        assert result["Return [%]"] == pytest.approx(2.5)
        repeated = execute(Hold, data, zone)
        assert repeated["Sharpe Ratio"] == result["Sharpe Ratio"]
        results.append(result)
    assert results[0]["Sharpe Ratio"] != results[1]["Sharpe Ratio"]
    for name in ("EntryTime", "ExitTime"):
        assert (
            results[0]["_trades"][name]
            .dt.tz_convert("UTC")
            .equals(results[1]["_trades"][name].dt.tz_convert("UTC"))
        )
    pd.testing.assert_frame_equal(
        results[0]["_trades"].drop(columns=["EntryTime", "ExitTime"]),
        results[1]["_trades"].drop(columns=["EntryTime", "ExitTime"]),
    )


def test_local_hour_strategy_changes_with_chart_timezone_and_keeps_old_result():
    @backtest()
    class LocalHour(Strategy):
        def init(self):
            pass

        def next(self):
            hour = self.data_index[-1].hour
            if hour == 9:
                self.buy(qty=1)
            elif hour == 10:
                self.close_position()

    data = candles(pd.date_range("2026-01-05 01:00", periods=4, freq="h", tz="UTC"))
    shanghai = execute(LocalHour, data, "Asia/Shanghai")
    saved = shanghai["_trades"].copy(deep=True)
    utc = execute(LocalHour, data, "UTC")
    assert shanghai["# Trades"] == 1 and utc["# Trades"] == 0
    assert shanghai["_strategy"] is not utc["_strategy"]
    assert shanghai.attrs["backtest_snapshot"]["context"]["timezone"] == "Asia/Shanghai"
    assert utc.attrs["backtest_snapshot"]["context"]["timezone"] == "UTC"
    pd.testing.assert_frame_equal(shanghai["_trades"], saved)
