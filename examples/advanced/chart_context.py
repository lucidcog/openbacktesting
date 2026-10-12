"""Chart context: instrument, timeframe, local-time conditions, statistical day boundaries, and daylight saving time.

Fixed offline OHLC demonstrates context injection only; it does not provide market-data retrieval or multi-timeframe resampling.
"""

import pandas as pd

from openbacktesting import DataContext, EndPolicy, Strategy, Timeframe, backtest, inputs, runtime
from openbacktesting.broker import InstrumentSpec
from openbacktesting.portfolio import export_result


@backtest(cash=10_000, commission_value=0.2, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class ChartStrategy(Strategy):
    quantity = inputs.int(1, title="Quantity", minval=1)
    local_hours = inputs.bool(False, title="Local hour")

    def init(self):
        self.observed_timeframe = self.timeframe

    def next(self):
        if self.local_hours:
            # Matches the chart clock directly, without requiring manual conversion from UTC.
            hour = self.data_index[-1].hour
            if hour == 9 and not self.position:
                self.buy(qty=self.quantity)
            elif hour == 10 and self.position:
                self.close_position()
        elif len(self.data) == 2:
            self.buy(qty=self.quantity)


def timezone_examples():
    """Return actual run results for readers and example tests; leave the supplied UTC data unchanged."""
    schema = runtime.describe(globals())

    def run(data, zone, *, local_hours=False):
        request = {key: schema[key] for key in ("schemaVersion", "schemaHash")} | {
            "values": {"Quantity": 1, "Local hour": local_hours}
        }
        before = data.copy(deep=True)
        result = runtime.run(
            globals(),
            request,
            data=data,
            context=DataContext(Timeframe.hours(1), zone),
            instrument=InstrumentSpec(symbol="TIMEZONE"),
            settings={"cash": 1000, "commission_value": 0},
        )
        pd.testing.assert_frame_equal(data, before)
        expected = data.index.tz_convert(zone)
        strategy = result["_strategy"]
        for index in (strategy.data_index, strategy.data.index, strategy.df.index):
            assert index.equals(expected)
        return result

    def frame(index, prices):
        return pd.DataFrame(
            {
                "Open": prices,
                "High": [p + 1 for p in prices],
                "Low": [p - 1 for p in prices],
                "Close": prices,
            },
            index=index,
        )

    # 01:00 UTC is 09:00 in Shanghai; rerun with a new context after changing the chart timezone.
    data = frame(
        pd.date_range("2026-01-05 01:00", periods=4, freq="h", tz="UTC"),
        [100.0, 101.0, 102.0, 103.0],
    )
    local = {zone: run(data, zone, local_hours=True) for zone in ("Asia/Shanghai", "UTC")}
    assert local["Asia/Shanghai"]["# Trades"] == 1
    assert local["UTC"]["# Trades"] == 0
    for zone, result in local.items():
        print(
            f"Chart {zone}, first bar {result['_equity_curve'].index[0].isoformat()}, "
            f"Trades {int(result['# Trades'])} trades"
        )

    # During the clock rollback, the two 01:30 values are distinct bars; their offsets differ and their absolute times remain one hour apart.
    data = frame(
        pd.date_range("2026-11-01 04:30", periods=5, freq="h", tz="UTC"),
        [100.0, 101.0, 102.0, 103.0, 104.0],
    )
    dst = run(data, "America/New_York")
    repeated = dst["_equity_curve"].index[1:3]
    assert [time.isoformat() for time in repeated] == [
        "2026-11-01T01:30:00-04:00",
        "2026-11-01T01:30:00-05:00",
    ]
    assert repeated[1] - repeated[0] == pd.Timedelta(hours=1)
    print("Repeated New York hour:", [time.isoformat() for time in repeated])

    # Orders at fixed bar positions produce identical trades and equity; different chart dates change daily closing-equity groups.
    data = frame(
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
        [100.0, 100.0, 110.0, 120.0, 115.0, 125.0],
    )
    statistics = {zone: run(data, zone) for zone in ("UTC", "Asia/Shanghai")}
    for zone, expected in [
        ("UTC", [1000.0, 1005.0, 1015.0]),
        ("Asia/Shanghai", [1000.0, 1010.0, 1015.0]),
    ]:
        portfolio = export_result(statistics[zone])
        assert portfolio["context"]["timezone"] == zone
        buckets = portfolio["analysis"]["periodical"]["buckets"]["daily"]
        compounded = 1000.0
        closes = []
        for bucket in buckets:
            compounded *= 1 + bucket["equityReturn"]
            closes.append(compounded)
        assert all(abs(a - b) < 1e-9 for a, b in zip(closes, expected))
        equity = statistics[zone]["_equity_curve"].Equity
        assert equity.resample("D").last().tolist() == expected
        print(f"Statistics {zone}: daily closing equity {expected}, Sharpe {statistics[zone]['Sharpe Ratio']}")
    assert statistics["UTC"]["_equity_curve"].Equity.tolist() == (
        statistics["Asia/Shanghai"]["_equity_curve"].Equity.tolist()
    )
    assert statistics["UTC"]["Sharpe Ratio"] != statistics["Asia/Shanghai"]["Sharpe Ratio"]
    return {"local": local, "dst": dst, "statistics": statistics}


def main():
    schema = runtime.describe(globals())
    request = {key: schema[key] for key in ("schemaVersion", "schemaHash")} | {
        "values": {"Quantity": 2}
    }
    results = []
    for symbol, timeframe, frequency in (
        ("DAILY", Timeframe.days(1), "D"),
        ("INTRADAY", Timeframe.minutes(15), "15min"),
    ):
        data = pd.DataFrame(
            {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0},
            index=pd.date_range("2026-01-01", periods=8, freq=frequency, tz="UTC"),
        )
        result = runtime.run(
            globals(),
            request,
            data=data,
            context=DataContext(timeframe, "UTC"),
            instrument=InstrumentSpec(symbol=symbol),
            settings={"cash": 20_000},
        )
        assert result["_strategy"].observed_timeframe == timeframe
        assert result["_trades"]["Size"].iloc[0] == 2
        snapshot = result.attrs["backtest_snapshot"]
        assert snapshot["instrument"]["symbol"] == symbol
        assert snapshot["settings"]["commission_value"] == 0.2
        assert snapshot["settings"]["cash"] == 20_000
        print(result[["Return [%]", "# Trades"]])
        results.append(result)
    timezone_examples()
    return results


if __name__ == "__main__":
    main()
