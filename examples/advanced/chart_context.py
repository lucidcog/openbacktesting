"""图表上下文：品种、周期、当地时间条件、统计日界与夏令时。

固定离线 OHLC 只用于展示注入机制，不代表行情获取或多周期重采样能力。
"""

import pandas as pd
from openbacktesting import DataContext, EndPolicy, Strategy, Timeframe, backtest, inputs, runtime
from openbacktesting.broker import InstrumentSpec
from openbacktesting.portfolio import export_result


@backtest(cash=10_000, commission_value=0.2, end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE)
class ChartStrategy(Strategy):
    quantity = inputs.int(1, title="数量", minval=1)
    local_hours = inputs.bool(False, title="按当地小时")

    def init(self):
        self.observed_timeframe = self.timeframe

    def next(self):
        if self.local_hours:
            # 直接对应图表钟点，作者无需从 UTC 手动转换。
            hour = self.data_index[-1].hour
            if hour == 9 and not self.position:
                self.buy(qty=self.quantity)
            elif hour == 10 and self.position:
                self.close_position()
        elif len(self.data) == 2:
            self.buy(qty=self.quantity)


def timezone_examples():
    """返回真实运行结果，供读者及示例测试核对；不修改传入的 UTC 数据。"""
    schema = runtime.describe(globals())

    def run(data, zone, *, local_hours=False):
        request = {key: schema[key] for key in ("schemaVersion", "schemaHash")} | {
            "values": {"数量": 1, "按当地小时": local_hours}
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

    # 01:00 UTC 对应上海 09:00；切换图表时区后用新 context 重新运行。
    data = frame(
        pd.date_range("2026-01-05 01:00", periods=4, freq="h", tz="UTC"),
        [100.0, 101.0, 102.0, 103.0],
    )
    local = {zone: run(data, zone, local_hours=True) for zone in ("Asia/Shanghai", "UTC")}
    assert local["Asia/Shanghai"]["# Trades"] == 1
    assert local["UTC"]["# Trades"] == 0
    for zone, result in local.items():
        print(
            f"图表 {zone}，首根 {result['_equity_curve'].index[0].isoformat()}，"
            f"交易 {int(result['# Trades'])} 笔"
        )

    # 回拨时两个 01:30 是不同 bar；偏移不同，绝对时间仍相差一小时。
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
    print("纽约重复小时：", [time.isoformat() for time in repeated])

    # 固定按 bar 下单，交易和权益一致；图表日期不同，每日末权益分组不同。
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
        print(f"统计 {zone}：每日末权益 {expected}，Sharpe {statistics[zone]['Sharpe Ratio']}")
    assert statistics["UTC"]["_equity_curve"].Equity.tolist() == (
        statistics["Asia/Shanghai"]["_equity_curve"].Equity.tolist()
    )
    assert statistics["UTC"]["Sharpe Ratio"] != statistics["Asia/Shanghai"]["Sharpe Ratio"]
    return {"local": local, "dst": dst, "statistics": statistics}


def main():
    schema = runtime.describe(globals())
    request = {key: schema[key] for key in ("schemaVersion", "schemaHash")} | {
        "values": {"数量": 2}
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
