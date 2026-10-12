"""Portfolio真实交易、报告口径、因果边界及纯值回归。"""

import json
import pickle

import numpy as np
import pandas as pd
import pytest
from openbacktesting import Backtest, Strategy
from openbacktesting.broker import Commission, InstrumentSpec
from openbacktesting.lib import compute_stats
from openbacktesting.portfolio import export_result, get_snapshot


def data(prices=(100.0, 112.0, 98.0, 102.0, 100.0), *, index=None, wide=False):
    return pd.DataFrame(
        {
            "Open": prices,
            "High": np.array(prices) + (10 if wide else 0),
            "Low": np.array(prices) - (10 if wide else 0),
            "Close": prices,
        },
        index=index if index is not None else pd.date_range("2026-01-01", periods=len(prices)),
    )


class Partial(Strategy):
    def init(self):
        pass

    def next(self):
        if self.bar_index == 0:
            self.buy(qty=3, tag={"signal": "entry", "nested": [1]})
        if self.bar_index in (1, 2, 3):
            self.trades[0].close(qty=1)


class Idle(Strategy):
    def init(self):
        pass

    def next(self):
        pass


def assert_account(p):
    initial = p["summary"]["all"]["initialCapital"]["value"]
    last = p["series"]["account"][-1]
    closed = p["trades"]["closedFragments"]
    opened = p["trades"]["openLots"]
    assert last["equity"] - initial == pytest.approx(
        sum(t["pnlNet"] for t in closed) + sum(t["openPnlNet"] for t in opened)
    )
    assert sum(f["fee"] for f in p["facts"]["fills"]) == pytest.approx(
        sum(a["fee"] for a in p["facts"]["allocations"])
    )
    for r, l, s in zip(
        p["series"]["account"],
        p["series"]["directions"]["long"],
        p["series"]["directions"]["short"],
    ):
        assert r["equity"] - initial == pytest.approx(l["contribution"] + s["contribution"])
    json.dumps(p, allow_nan=False)


def test_partial_fees_identity_freeze_and_methods():
    r = Backtest(
        data(), Partial, cash=1000, execution_timing="same_close", commission=Commission(per_unit=1)
    ).run()
    p = export_result(r)
    assert_account(p)
    trades = p["trades"]["closedFragments"]
    assert len(trades) == 3 and len({t["lotId"] for t in trades}) == 1
    assert len({t["fragmentId"] for t in trades}) == 3
    assert [t["pnlNet"] for t in trades] == [10, -4, 0]
    assert p["summary"]["all"]["profitFactorMoney"]["value"] == 2.5
    assert p["summary"]["all"]["feesPaid"]["value"] == 6
    assert p["summary"]["long"]["feesPaid"]["value"] == 6
    assert p["summary"]["all"]["totalPnlGross"]["value"] == 12
    assert p["summary"]["all"]["closedReturn"]["value"] == 0.006
    assert p["summary"]["all"]["buyHoldPnl"]["value"] == 0
    assert p["summary"]["all"]["marginCalls"]["status"] == "unsupported"
    assert p["analysis"]["distribution"]["evens"] == 1
    assert p["trades"]["closedFragments"][0]["entry"]["signal"] == "entry"
    frozen = get_snapshot(r)
    assert pickle.loads(pickle.dumps(frozen)) == frozen
    with pytest.raises(AttributeError):
        frozen._payload = "{}"
    p["trades"]["closedFragments"][0]["extensions"]["Tag"]["nested"].append(9)
    r["_trades"].loc[0, "PnL"] = 999
    assert export_result(r)["trades"]["closedFragments"][0]["pnlNet"] == 10
    r.pop("_strategy")
    assert get_snapshot(r) == frozen


@pytest.mark.parametrize(
    "index", [pd.RangeIndex(5), pd.date_range("2026-01-01", periods=5, tz="Asia/Shanghai")]
)
def test_empty_and_ordinal(index):
    r = Backtest(data(index=index), Idle, plotting=False).run()
    p = export_result(r)
    assert_account(p)
    assert p["summary"]["all"]["totalPnl"]["value"] == 0
    assert p["summary"]["all"]["winRate"]["value"] is None
    assert p["series"]["benchmark"]["first_entry_price"]["status"] == "not_applicable"
    assert p["analysis"]["streaks"]["rows"] == []
    assert p["analysis"]["growthAndDecline"]["drawdowns"] == []
    assert p["analysis"]["timePatterns"]["status"] == (
        "ok" if isinstance(index, pd.DatetimeIndex) else "not_applicable"
    )


class Reverse(Strategy):
    def init(self):
        pass

    def next(self):
        if self.bar_index == 0:
            self.buy(qty=2, tag="long")
        if self.bar_index == 1:
            self.sell(qty=3, tag="short")


@pytest.mark.parametrize("hedging", [False, True])
@pytest.mark.parametrize("fee", [1.0, -1.0])
@pytest.mark.parametrize("timing", ["same_close", "next_open"])
def test_reverse_account_and_terminal(hedging, fee, timing):
    p = export_result(
        Backtest(
            data(),
            Reverse,
            hedging=hedging,
            commission=lambda qty, price: abs(qty) * fee,
            execution_timing=timing,
            end_policy="close_at_last_close",
        ).run()
    )
    assert_account(p)
    assert not p["trades"]["openLots"]
    assert p["series"]["account"][-1]["phase"] == "terminal"
    assert p["analysis"]["liquidations"]["end_liquidation"]["quantity"] > 0


def test_open_trade_excursion_excludes_before_entry():
    class Hold(Idle):
        def next(self):
            if self.bar_index == 0:
                self.buy(qty=1)

    p = export_result(
        Backtest(
            data([100.0], wide=True),
            Hold,
            execution_timing="same_close",
            commission=Commission(fixed=1),
        ).run()
    )
    assert_account(p)
    t = p["trades"]["openLots"][0]
    assert t["exit"] is None and t["excursion"]["mfeMoney"] == 0 and t["excursion"]["maeMoney"] == 0
    assert p["summary"]["all"]["feesPaid"]["value"] == 1


def test_recompute_snapshot_and_subset():
    d = data(index=pd.date_range("2026-01-01", periods=5, freq="MS", tz="UTC"))
    r = Backtest(d, Partial, execution_timing="same_close").run()
    changed = compute_stats(stats=r, data=d, risk_free_rate=0.02)
    assert export_result(changed)["semantics"]["riskFreeRate"] == 0.02
    assert export_result(r)["semantics"]["riskFreeRate"] == 0
    sub = compute_stats(stats=r, data=d, trades=r["_trades"].iloc[:1])
    with pytest.raises(ValueError, match="snapshot_missing"):
        export_result(sub)
    with pytest.raises(ValueError, match="snapshot_missing"):
        export_result(pd.Series())


def test_conditional_partial_and_quantity_grid():
    class Conditional(Idle):
        def next(self):
            if self.bar_index == 0:
                self.buy(qty=1, limit=99, tag={"signal": 7})
            if self.bar_index == 2 and self.trades:
                self.trades[0].close()

    p = export_result(
        Backtest(
            data(wide=True), Conditional, instrument=InstrumentSpec(quantity_step=1, min_notional=1)
        ).run()
    )
    assert_account(p)
    assert p["trades"]["closedFragments"][0]["excursion"]["coverage"] == "partial"
    assert p["trades"]["closedFragments"][0]["entry"]["signal"] is None


def test_profit_factor_baseline():
    from openbacktesting.portfolio.stats import compute_stats as raw

    idx = pd.date_range("2026-01-01", periods=4)
    trades = pd.DataFrame(
        {
            "Size": [10, 1],
            "EntryBar": [0, 1],
            "ExitBar": [2, 3],
            "PnL": [100.0, -20.0],
            "ReturnPct": [0.1, -0.2],
            "Duration": [pd.Timedelta(days=2)] * 2,
        }
    )
    r = raw(
        trades,
        np.array([1000.0, 1000.0, 1100.0, 1080.0]),
        pd.DataFrame({"Close": [100.0, 101.0, 99.0, 100.0]}, index=idx),
        None,
        initial_equity=1000.0,
    )
    assert r["Profit Factor"] == 0.5


def test_statistics_formulas_and_edges():
    from openbacktesting.portfolio.metrics import (
        correlation,
        monthly_risk,
        path_metrics,
        trade_metrics,
    )

    trades = [
        {
            "fragmentId": "a",
            "lotId": "x",
            "pnlNet": 100.0,
            "returnFraction": 0.1,
            "feeTotal": 2.0,
            "barsHeld": 2,
            "durationNs": "10",
        },
        {
            "fragmentId": "b",
            "lotId": "y",
            "pnlNet": -20.0,
            "returnFraction": -0.2,
            "feeTotal": 1.0,
            "barsHeld": 1,
            "durationNs": "20",
        },
    ]
    values = trade_metrics(trades, [])
    assert values["profitFactorMoney"]["value"] == 5
    assert values["averageTradeDurationNs"]["value"] == "15"
    assert values["largestProfit"]["reference"] == "a"
    assert values["largestLossReturn"]["reference"] == "b"
    for profits, expected, reason in [
        ([1.0, 2.0], None, "unbounded"),
        ([-1.0, -2.0], 0, None),
        ([0.0, 0.0], None, "zero_denominator"),
    ]:
        ts = [t | {"pnlNet": profit} for t, profit in zip(trades, profits)]
        pf = trade_metrics(ts, [])["profitFactorMoney"]
        assert pf["value"] == expected and pf["reason"] == reason
    returns = [0.1, -0.05, 0.2]
    risk = monthly_risk([{"equityReturn": r} for r in returns], 0.12)
    excess = np.array(returns) - ((1.12) ** (1 / 12) - 1)
    assert risk["sharpe"]["value"] == pytest.approx(excess.mean() / np.std(returns) * np.sqrt(12))
    assert risk["sortino"]["value"] == pytest.approx(
        excess.mean() / np.sqrt(np.mean(np.minimum(excess, 0) ** 2)) * np.sqrt(12)
    )
    assert monthly_risk([{"equityReturn": None}] * 2, 0)["sharpe"]["status"] == "insufficient_data"
    assert monthly_risk([{"equityReturn": 0}] * 2, 0)["sharpe"]["reason"] == "zero_denominator"
    assert correlation([0, 1, None], [0, 2, 5])["value"] == pytest.approx(1)
    assert correlation([1, 1], [1, 2])["value"] is None
    rows = [{"equity": v, "observationId": str(i)} for i, v in enumerate([100, 150, 75, 180])]
    m = path_metrics(rows, 100)
    assert m["maxDrawdown"]["value"] == 75 and m["maxRunup"]["value"] == 105
    assert m["maxRunupFraction"]["value"] == 1.4


def test_analysis_boundaries_and_interval_semantics():
    from openbacktesting.portfolio.analysis import distribution, episodes, streaks, time_patterns

    values = [0.0, 0.01, 0.01, 0.01, 0.5, -0.01]
    trades = [
        {
            "fragmentId": str(i),
            "pnlNet": v * 100,
            "returnFraction": v,
            "entry": {"barIndex": i},
            "barsHeld": 1,
        }
        for i, v in enumerate(values)
    ]
    d = distribution(trades)
    assert [r["lower"] for r in d["histogram"]] == [-0.01, 0.0, 0.01, 0.5]
    assert d["outliers"]["fragmentIds"] == ["4", "5"]
    same = distribution([t | {"returnFraction": 0.01} for t in trades])
    assert same["outliers"]["fragmentIds"] == []
    st = streaks(trades)
    assert st["summary"]["winning"]["longest"] == 4
    assert st["summary"]["winning"]["maximumAmount"] == 53
    assert st["rows"][-1]["current"] is True
    assert not any(r["current"] for r in streaks(trades + [trades[0]])["rows"])
    idx = pd.to_datetime(["2026-11-01T05:30Z", "2026-11-01T06:30Z"] * 3).tz_convert(
        "America/New_York"
    )
    times = time_patterns(trades, idx)
    assert times["groups"]["hours"]["rows"][1]["count"] == 6
    assert times["groups"]["hours"]["bestKeys"] == [1]
    rows = [
        {
            "equity": v,
            "observationId": str(i),
            "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=i),
        }
        for i, v in enumerate([99, 110, 100, 105, 110, 90, 90])
    ]
    e = episodes(rows, 100)
    assert [(r["amount"], r["current"]) for r in e["drawdowns"]] == [
        (1, False),
        (10, False),
        (20, True),
    ]
    assert e["summary"]["drawdown"]["maximum"] == 20
    assert e["summary"]["growth"]["maximum"] == 11
    assert episodes([], 100) == {"drawdowns": [], "alternating": []}
    for r in rows:
        r["timestamp"] = int(r["observationId"])
    assert episodes(rows, 100)["summary"]["drawdown"]["averageDurationNs"] is None
    negative = [r | {"equity": v} for r, v in zip(rows, [0, -1, 1, 0, -2, -1, 0])]
    assert any(r["fraction"] is None for r in episodes(negative, 100)["alternating"])


def test_encoder_precision_status_and_rejection():
    from openbacktesting.portfolio.models import metric, plain, time_ref

    assert plain({"na": pd.NA, "nat": pd.NaT, "inf": float("inf")}) == {
        "na": None,
        "nat": None,
        "inf": None,
    }
    assert plain(np.int64(2**60)) == str(2**60)
    assert plain(pd.Timedelta(1, "ns")) == "1"
    assert plain((True, 1.0, "x")) == [True, 1.0, "x"]
    assert time_ref(pd.Timestamp("2026-01-01").as_unit("s"))["value"] == str(
        pd.Timestamp("2026-01-01").value
    )
    assert metric(float("nan"))["reason"] == "undefined_value"
    with pytest.raises(TypeError, match="纯值编码"):
        plain(object())


def test_observers_leave_execution_and_callbacks_unchanged():
    class Traced(Reverse):
        def init(self):
            self.trace = []

        def on_order(self, event):
            self.trace.append(("order", event))

        def on_fill(self, event):
            self.trace.append(("fill", event))

    enabled = Backtest(
        data(wide=True), Traced, execution_timing="same_close", end_policy="close_at_last_close"
    )
    disabled = Backtest(
        data(wide=True), Traced, execution_timing="same_close", end_policy="close_at_last_close"
    )
    disabled._portfolio_enabled = False
    a, b = enabled.run(), disabled.run()
    assert a["_strategy"].trace == b["_strategy"].trace
    for name in [
        "_orders",
        "_order_events",
        "_order_sizing",
        "_fills",
        "_trade_allocations",
        "_account_curve",
        "_positions",
        "_trades",
    ]:
        pd.testing.assert_frame_equal(a[name], b[name])
    assert "portfolio_snapshot" not in b.attrs


def test_partial_exit_freezes_extrema_and_open_gap_exit():
    class PartialHold(Idle):
        def next(self):
            if self.bar_index == 0:
                self.buy(qty=2)
            if self.bar_index == 1:
                self.trades[0].close(qty=1)

    p = export_result(
        Backtest(
            data([100.0, 110.0, 140.0], wide=True), PartialHold, execution_timing="same_close"
        ).run()
    )
    assert p["trades"]["closedFragments"][0]["excursion"]["mfeMoney"] == 20
    assert p["trades"]["openLots"][0]["excursion"]["mfeMoney"] == 50

    class OpenExit(Idle):
        def next(self):
            if self.bar_index == 0:
                self.buy(qty=1)
            if self.bar_index == 1:
                self.trades[0].close()

    p = export_result(Backtest(data([100.0, 110.0, 150.0], wide=True), OpenExit).run())
    assert p["trades"]["closedFragments"][0]["excursion"]["mfeMoney"] == 40


def test_insolvency_stops_new_paths_and_benchmark():
    class Short(Idle):
        def next(self):
            if self.bar_index == 0:
                self.sell(qty=9)

    p = export_result(
        Backtest(
            data([100.0, 100.0, 500.0, 900.0]), Short, cash=1000, execution_timing="same_close"
        ).run()
    )
    assert p["run"]["terminationReason"] == "insolvent"
    assert p["run"]["processedThroughBar"] == 2
    assert p["series"]["benchmark"]["input_start_close"]["points"][-1]["barIndex"] == 2
    assert p["summary"]["all"]["cagr"]["value"] is None
    assert p["analysis"]["liquidations"]["insolvent"]["quantity"] == 9
    assert_account(p)


def test_periodical_calendar_carry_and_benchmark_minimum():
    from openbacktesting import DataContext, Timeframe

    idx = pd.to_datetime(["2026-01-31T22:00Z", "2026-03-01T01:00Z", "2026-04-01T01:00Z"])
    p = export_result(
        Backtest(
            data([100.0, 120.0, 110.0], index=idx),
            Idle,
            context=DataContext(Timeframe.days(1), "America/New_York"),
            instrument=InstrumentSpec(min_notional=100000),
            cash=1000,
        ).run()
    )
    months = p["analysis"]["periodical"]["buckets"]["monthly"]
    assert len(months) == 3 and not months[1]["carriedForward"]
    assert p["context"]["dataContext"]["timezone"] == "America/New_York"
    assert p["series"]["benchmark"]["input_start_close"]["quantity"] == 0
    daily = p["analysis"]["periodical"]["buckets"]["daily"]
    assert any(r["carriedForward"] for r in daily)
    assert sum(r["fees"] for r in daily) == 0


def test_snapshot_paths_catalog_and_callable_optimization():
    from openbacktesting.portfolio import report_catalog

    catalog = report_catalog()
    p = export_result(Backtest(data(), Partial, execution_timing="same_close").run())
    for entry in catalog["entries"]:
        current = p
        for segment in entry["path"]:
            current = current[segment]
    assert {e["id"] for e in catalog["entries"] if e["region"] == "Metrics"} == set(
        p["summary"]["all"]
    )

    class Param(Partial):
        n = 1

    seen = []

    def score(result):
        seen.append(export_result(result)["schemaVersion"])
        return result["Equity Final [$]"]

    from multiprocessing.dummy import Pool

    import openbacktesting

    old = openbacktesting.Pool
    openbacktesting.Pool = Pool
    try:
        r = Backtest(data(), Param, execution_timing="same_close").optimize(
            n=[1, 2], maximize=score
        )
        assert seen == ["1.0.0"] * 2
        assert export_result(r)["schemaVersion"] == "1.0.0"
    finally:
        openbacktesting.Pool = old


def test_refresh_without_snapshot():
    from openbacktesting.portfolio.snapshot import refresh_snapshot

    historical = pd.Series({"Equity Final [$]": 1000.0})
    refresh_snapshot(historical)
    assert historical.attrs == {}


def test_record_copy_keeps_only_declared_facts():
    from dataclasses import asdict

    from openbacktesting.broker.models import AccountSnapshot, record

    value = AccountSnapshot(100.0, 101.0, 1.0, 0.0, 0.0, 10.0, 91.0, 10.0, 10.0)
    object.__setattr__(value, "extra", "ignored")
    copy = record(value)
    assert copy == asdict(value)
    copy["equity"] = 0
    assert value.equity == 101


def test_catalog_inventory_and_live_contract():
    from openbacktesting.portfolio import report_catalog

    catalog = report_catalog()
    ids = {entry["id"] for entry in catalog["entries"]}
    assert set(catalog["regions"]) == {
        "Key stats",
        "Performance",
        "Breakdown",
        "Periodical",
        "Benchmarking",
        "Margin usage",
        "Growth and decline",
        "Distribution",
        "Streaks",
        "Time patterns",
        "List of Trades",
    }
    assert all(set(fields) <= ids for fields in catalog["regions"].values())
    assert len(catalog["tradeColumns"]) == 14
    copy = report_catalog()
    copy["entries"].clear()
    assert report_catalog()["entries"]
    for index in (
        pd.RangeIndex(5),
        pd.date_range("2026-11-01T04:30Z", periods=5, freq="h").tz_convert("America/New_York"),
        pd.date_range("2026-01-01", periods=5),
    ):
        p = export_result(Backtest(data(index=index), Partial, execution_timing="same_close").run())
        json.dumps(p, allow_nan=False)


def test_same_bar_roundtrip_execution_peak_and_hedged_extrema():
    class Roundtrip(Idle):
        def next(self):
            if self.bar_index == 0:
                self.buy(qty=2, tag="entry")
                self.sell(qty=2, tag="exit")

    p = export_result(
        Backtest(
            data([100.0]),
            Roundtrip,
            cash=1000,
            execution_timing="same_close",
            commission=Commission(fixed=1),
        ).run()
    )
    summary = p["summary"]["all"]
    assert summary["maxGrossQuantity"]["value"] == 2
    assert summary["maxMarginUsed"]["value"] == 200
    assert summary["averageMarginUsed"]["value"] == 0
    assert summary["observedCapitalRequired"]["value"] == 201
    assert summary["intrabar.maxDrawdown"]["value"] == 2
    trade = p["trades"]["closedFragments"][0]
    assert (trade["barsElapsed"], trade["barsHeld"]) == (0, 1)
    assert trade["exit"]["signal"] == "exit"

    class Hedge(Idle):
        def next(self):
            if self.bar_index == 0:
                self.buy(qty=1)
                self.sell(qty=1)

    p = export_result(
        Backtest(
            data([100.0, 100.0], wide=True),
            Hedge,
            cash=1000,
            execution_timing="same_close",
            hedging=True,
        ).run()
    )
    assert sum(t["excursion"]["maeMoney"] for t in p["trades"]["openLots"]) == 20
    assert p["summary"]["all"]["intrabar.maxDrawdown"]["value"] == 0
    assert p["summary"]["all"]["maxMarginUsed"]["value"] == 220
    assert_account(p)


def test_largest_amount_and_return_reference_are_independent():
    from openbacktesting.portfolio.metrics import trade_metrics

    common = {"lotId": "lot", "feeTotal": 0.0, "barsHeld": 1, "durationNs": "0"}
    trades = [
        common | {"fragmentId": "large", "pnlNet": 100, "returnFraction": 0.01},
        common | {"fragmentId": "rate", "pnlNet": 10, "returnFraction": 0.1},
    ]
    m = trade_metrics(trades, [])
    assert m["largestProfit"]["reference"] == "large"
    assert m["largestProfitReturn"]["reference"] == "rate"
    assert m["largestProfitShare"]["value"] == pytest.approx(100 / 110)


def test_unfilled_requests_and_nanosecond_freeze():
    idx = pd.date_range("2026-11-01T05:30Z", periods=3, freq="h").tz_convert(
        "America/New_York"
    ) + pd.Timedelta(123, "ns")

    class Requests(Idle):
        def next(self):
            if self.bar_index == 0:
                self.buy(qty=1000)
                self.buy(qty=1, limit=1, expires_at=idx[2])
                self.buy(qty=1, limit=2).cancel()

    frame = data([100.0, 100.0, 100.0], index=idx)
    result = Backtest(frame, Requests, cash=1000, execution_timing="same_close").run()
    before = export_result(result)
    frame.iloc[:, :] = 200
    result["_orders"].loc[0, "reason"] = "edited"
    assert export_result(result) == before
    assert [r["status"] for r in before["facts"]["orders"]] == ["Rejected", "Expired", "Canceled"]
    assert not before["facts"]["fills"] and not before["trades"]["closedFragments"]
    assert before["run"]["inputRange"][0]["value"] == str(idx[0].value)
    assert before["facts"]["orders"][1]["expires_at"]["value"] == str(idx[2].value)
    assert before["context"]["timezone"] == "America/New_York"


def test_large_integer_trade_metadata_is_lossless():
    class Large(Idle):
        def next(self):
            if self.bar_index == 0:
                self.buy(qty=2, tag={"integer": 2**60})
            if self.bar_index == 1:
                self.trades[0].close(qty=1)

    result = Backtest(data(), Large, execution_timing="same_close").run()
    report = export_result(result)
    assert report["trades"]["openLots"][0]["tag"]["integer"] == str(2**60)
    assert report["trades"]["closedFragments"][0]["extensions"]["Tag"]["integer"] == str(2**60)


def test_histogram_decimal_boundaries_match_exported_intervals():
    from openbacktesting.portfolio.analysis import distribution

    returns = [0.29, 0.7, -0.29, -0.3, 0.3]
    rows = [
        {"fragmentId": str(i), "returnFraction": r, "pnlNet": r * 100}
        for i, r in enumerate(returns)
    ]
    histogram = distribution(rows)["histogram"]
    assert [b["lower"] for b in histogram] == [-0.3, -0.29, 0.29, 0.3, 0.7]
    for b in histogram:
        assert all(b["lower"] <= returns[int(ref)] < b["upper"] for ref in b["fragmentIds"])


def test_intrabar_bounds_use_known_extrema_without_assuming_order():
    from openbacktesting.portfolio.metrics import path_metrics

    rows = [
        {"equity": v, "observationId": str(i), "barIndex": 0, "ordered": i not in (1, 2)}
        for i, v in enumerate([100.0, 110.0, 90.0, 100.0])
    ]
    bounds = path_metrics(rows, 100, approximate=True)
    assert bounds["maxDrawdown"]["value"] == 10
    assert bounds["maxRunup"]["value"] == 10
    assert bounds["maxDrawdown"]["status"] == "approximate"
    rows[1], rows[2] = rows[2], rows[1]
    assert path_metrics(rows, 100, approximate=True) == bounds
    rows[-1]["equity"] = 80
    assert path_metrics(rows, 100, approximate=True)["maxDrawdown"]["value"] == 30


def test_nonpositive_runup_base_is_undefined_instead_of_zero():
    from openbacktesting.portfolio.metrics import path_metrics

    rows = [{"observationId": str(i), "equity": v} for i, v in enumerate([100.0, -10.0, -5.0])]
    for approximate in (False, True):
        result = path_metrics(rows, 100, approximate=approximate)
        assert result["maxRunup"]["value"] == 5
        assert result["maxRunupFraction"]["value"] is None
        assert result["maxRunupFraction"]["status"] == "undefined"
        assert result["maxRunupFraction"]["reason"] == "nonpositive_runup_base"


@pytest.mark.parametrize("reversed_range", [False, True])
@pytest.mark.parametrize("size", [1, -1])
@pytest.mark.parametrize(
    "conditional, phase", [(False, "execute"), (False, "close"), (True, "execute")]
)
def test_bar_extrema_keep_direction_first_tie_and_entry_boundary(
    size, conditional, phase, reversed_range
):
    from types import SimpleNamespace

    from openbacktesting.broker.observations import Observations

    trade = SimpleNamespace(trade_id=1, size=size, entry_price=100.0)
    broker = SimpleNamespace(_i=0, trades=[trade], last_price=100.0)
    observations = Observations()
    observations.opened(broker, trade, conditional, phase)
    eligible_prices = []
    # 首根范围更大；条件/收盘入场只能看首根收盘，后续并列保留第一次。
    for bar, (high, low) in enumerate([(120, 80), (105, 95), (109, 91), (109, 91), (103, 90)]):
        broker._i = bar
        if reversed_range:
            high, low = low, high
        broker._data = SimpleNamespace(_current_value={"High": high, "Low": low}.__getitem__)
        observations.mark_bar(broker)
        included = [100.0] if bar == 0 and (conditional or phase == "close") else [high, low]
        eligible_prices.extend((bar, (price - 100.0) * size) for price in included)
        best = max([(0, 0.0), *eligible_prices], key=lambda item: item[1])
        worst = min([(0, 0.0), *eligible_prices], key=lambda item: item[1])
        state = observations.lots[1]
        assert (state["mfe"], state["mfeBar"]) == (best[1], best[0])
        assert (state["mae"], state["maeBar"]) == (-worst[1], worst[0])
        assert state["partial"] is conditional
