"""Log host sessions, parameter discovery, and real optimization isolation."""

import json
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.dummy import Pool as ThreadPool

import pytest
from test_backtest_declaration import chart, namespace
from test_engine_edges import Idle, flat_data
from test_inputs import request
from test_strategy_logs import LoggingTrade

import openbacktesting as api
from openbacktesting import Backtest, RunLogs, backtest, runtime
from openbacktesting.lib import MultiBacktest
from openbacktesting.portfolio.stats import dummy_stats
from openbacktesting.test import GOOG


@backtest()
class DeclaredLogs(LoggingTrade):
    pass


class SearchLogs(Idle):
    parameter = 1
    fail = ""

    def init(self):
        self.log.info(f"Parameter={self.parameter}")
        if self.fail == "candidate" and not self._log._collector.enabled:
            raise ValueError("Candidate failure")
        if self.fail == "final" and self._log._collector.enabled:
            raise ValueError("Final failure")
        if self.fail == "invalid":
            self.log.info(1)

    def next(self):
        self.log.info(f"Parameter={self.parameter}")
        if self.bar_index == 0:
            self.buy(qty=self.parameter)
        if self.bar_index == 4:
            self.close_position()


def test_runtime_success_defaults_copy_and_failure_reuse():
    session = RunLogs()
    assert session.get_logs() == []
    result = runtime.run(namespace(DeclaredLogs), logs=session, **chart())
    original = session.get_logs()
    assert original == result.attrs["strategy_logs"]
    result.attrs["strategy_logs"].clear()
    assert session.get_logs() == original
    for overrides in [
        {"namespace": {}},
        {"settings": {"unknown": 1}},
        {"context": None},
        {"instrument": None},
        {"request": {}},
        {"data": flat_data(0)},
        {"options": {"logs": session}},
    ]:
        args = {"namespace": namespace(DeclaredLogs), "logs": session} | chart() | overrides
        with pytest.raises((TypeError, ValueError)):
            runtime.run(**args)
        assert session.get_logs() == []
    # Recover the same session after failure without retaining old records.
    result = runtime.run(
        namespace(DeclaredLogs), request(DeclaredLogs, {"Quantity": 2}), logs=session, **chart()
    )
    assert result.attrs["strategy_logs"] == session.get_logs()
    assert session.get_logs()[0]["sequence"] == 1
    assert original[0]["message"] == "Initialization"
    without = runtime.run(namespace(DeclaredLogs), **chart())
    assert without.attrs["strategy_logs"]
    json.dumps(session.get_logs(), allow_nan=False)
    with pytest.raises(TypeError, match="RunLogs"):
        runtime.run(namespace(DeclaredLogs), logs={}, **chart())


@pytest.mark.parametrize("supplied", [False, True])
def test_runtime_original_exception_and_finish_logs(supplied):
    primary = ValueError("Author exception")

    @backtest()
    class Fail(Idle):
        def init(self):
            self.log.info("Before failure")
            raise primary

        def on_finish(self, summary):
            self.log.warning("Exception end")

    session = RunLogs()
    with pytest.raises(ValueError) as caught:
        runtime.run(namespace(Fail), logs=session if supplied else None, **chart())
    assert caught.value is primary and not hasattr(primary, "logs")
    if supplied:
        assert [r["message"] for r in session.get_logs()] == ["Before failure", "Exception end"]


def test_active_session_reentry_and_concurrent_use():
    session = RunLogs()

    @backtest()
    class Reenter(Idle):
        def init(self):
            self.log.info("Owner")

            def attempt():
                with pytest.raises(RuntimeError, match="occupied"):
                    runtime.run(namespace(Reenter), logs=session, **chart())

            attempt()
            with ThreadPoolExecutor(1) as pool:
                pool.submit(attempt).result()

    result = runtime.run(namespace(Reenter), logs=session, **chart())
    assert session.get_logs() == result.attrs["strategy_logs"]
    assert len(session.get_logs()) == 1
    runtime.run(namespace(DeclaredLogs), logs=session, **chart())
    assert len(session.get_logs()) > 1


def test_describe_and_stats_do_not_execute_author(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("describe must not execute the author")

    monkeypatch.setattr(DeclaredLogs, "init", forbidden)
    monkeypatch.setattr(DeclaredLogs, "__init__", forbidden)
    assert runtime.describe(namespace(DeclaredLogs))["backtest"]
    assert dummy_stats().index.size > 1


@pytest.mark.parametrize("mode", ["thread", "spawn", "default"])
def test_grid_only_final_and_no_trade_fallback(monkeypatch, mode):
    if mode != "default":
        factory = ThreadPool if mode == "thread" else mp.get_context("spawn").Pool
        monkeypatch.setattr(api, "Pool", lambda: factory(2))
    bt = Backtest(GOOG.iloc[:8], SearchLogs)
    bt.run(parameter=3)
    selected, heatmap = bt.optimize(parameter=[1, 2], maximize="Return [%]", return_heatmap=True)
    records = bt.get_logs()
    assert len(records) == 9 and records == selected.attrs["strategy_logs"]
    assert {r["message"] for r in records} == {f"Parameter={heatmap.idxmax()[0]}"}
    assert records[0]["sequence"] == 1
    declared = Backtest(GOOG.iloc[:8], LoggingTrade)
    result = declared.optimize(enabled=[False], units=[1, 2], maximize="Return [%]")
    assert result["# Trades"] == 0
    assert declared.get_logs() == result.attrs["strategy_logs"]
    assert len(declared.get_logs()) == 11


@pytest.mark.parametrize("method", ["grid", "sambo"])
@pytest.mark.parametrize("fail", ["candidate", "final", "invalid"])
def test_search_failure_and_recovery(monkeypatch, method, fail):
    monkeypatch.setattr(api, "Pool", lambda: ThreadPool(2))
    bt = Backtest(GOOG.iloc[:8], SearchLogs)
    bt.run()
    error = TypeError if fail == "invalid" else ValueError
    with pytest.raises(error):
        bt.optimize(
            parameter=[1, 2],
            fail=[fail],
            method=method,
            max_tries=8,
            maximize="Return [%]",
            random_state=0,
        )
    if fail == "final":
        assert len(bt.get_logs()) == 1
    else:
        assert bt.get_logs() == []
    result = bt.run()
    assert result.attrs["strategy_logs"] == bt.get_logs()
    assert len(bt.get_logs()) == 9
    with pytest.raises(ValueError, match="parameters"):
        bt.optimize()
    assert bt.get_logs() == []


def test_sambo_final_and_candidate_expression_semantics():
    bt = Backtest(GOOG.iloc[:8], SearchLogs)
    result = bt.optimize(
        parameter=[1, 2], method="sambo", max_tries=8, maximize="Return [%]", random_state=0
    )
    assert len(bt.get_logs()) == 9
    assert bt.get_logs() == result.attrs["strategy_logs"]
    seen = []

    class Expr(Idle):
        def init(self):
            self.log.info(f"{seen.append(self.parameter)}")

    bt = Backtest(flat_data(2), Expr)
    result = bt.optimize(
        parameter=[1, 2], method="sambo", max_tries=8, maximize="Return [%]", random_state=0
    )
    assert len(seen) > 1
    assert len(result.attrs["strategy_logs"]) == 1


def test_multi_backtest_stats_and_external_output(monkeypatch, capsys):
    monkeypatch.setattr(api, "Pool", lambda: ThreadPool(2))
    multi = MultiBacktest([GOOG.iloc[:8], GOOG.iloc[8:16]], SearchLogs)
    table = multi.run(parameter=1)
    for index, frame in enumerate([GOOG.iloc[:8], GOOG.iloc[8:16]]):
        assert (
            table[index]["Equity Final [$]"]
            == Backtest(frame, SearchLogs).run()["Equity Final [$]"]
        )
    assert "strategy_logs" not in table.index
    assert table.attrs.get("strategy_logs", []) == []

    class Output(Idle):
        def init(self):
            print("External output")
            self.log.info("Strategy logs")

    bt = Backtest(flat_data(2), Output)
    bt.run()
    assert [r["message"] for r in bt.get_logs()] == ["Strategy logs"]
    assert "External output" in capsys.readouterr().out
