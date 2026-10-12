"""复用范围、共享内存分配、失败清理及可写行情隔离。"""

import json
import subprocess
import sys
from multiprocessing.pool import ThreadPool
from pathlib import Path

import openbacktesting as api
import numpy as np
import pandas as pd
import pytest
from openbacktesting.indicators import runtime as indicators
from openbacktesting.parallel import SharedMemoryManager
from openbacktesting.simulation import optimization
from test_indicator_regressions import frame


class Repeated(api.Strategy):
    threshold = 1
    mutate = False

    def init(self):
        self.calls = 0
        self.total = len(self.data)
        if self.mutate:
            self.data.df.loc[:, "Close"] += self.threshold
        self.first = self.ta.sma(length=2)
        self.second = self.ta.sma(length=2)

    def next(self):
        assert self.bar_index == self.calls
        assert self.bar_state.is_first == (self.calls == 0)
        assert self.bar_state.is_last == (self.calls == self.total - 1)
        self.calls += 1
        if not self.position:
            self.buy(qty=1)


def test_thread_cache_reuse_shared_allocation_and_off_equivalence(monkeypatch):
    monkeypatch.setattr(api, "Pool", lambda: ThreadPool(2))
    monkeypatch.setattr(optimization, "_batch", lambda values: [[value] for value in values])
    calls, allocations = [], []
    execute, df2shm = indicators.execute, SharedMemoryManager.df2shm

    def counted(*args):
        calls.append(1)
        return execute(*args)

    def allocate(self, data):
        allocations.append(1)
        return df2shm(self, data)

    monkeypatch.setattr(indicators, "execute", counted)
    monkeypatch.setattr(SharedMemoryManager, "df2shm", allocate)
    data = frame(40)
    before = data.copy()
    results = []
    for budget in [64 * 1024 * 1024, 0]:
        calls.clear()
        bt = api.Backtest(
            data, Repeated, end_policy="close_at_last_close", indicator_cache_bytes=budget
        )
        stats, heatmap = bt.optimize(
            threshold=[1, 2, 3, 4], maximize="Equity Final [$]", return_heatmap=True
        )
        results.append((stats, heatmap))
        if budget:
            assert len(calls) == 2  # 一次优化共享计算 + 最优结果单独 run。
        else:
            assert len(calls) == 10
        assert not indicators._OPTIMIZATION_CACHES
    assert len(allocations) == 2  # 每次 optimize 一次，不随四个批次增长。
    pd.testing.assert_series_equal(results[0][1], results[1][1])
    pd.testing.assert_frame_equal(results[0][0]["_trades"], results[1][0]["_trades"])
    pd.testing.assert_frame_equal(data, before)
    calls.clear()
    bt = api.Backtest(data, Repeated, end_policy="close_at_last_close")
    bt.optimize(threshold=[1, 2, 3], mutate=[True], maximize="Equity Final [$]")
    assert len(calls) == 4  # 三份不同的运行私有数据与最终 run。
    pd.testing.assert_frame_equal(data, before)


def test_failed_run_closes_cursor_and_releases_cache():
    captured = []

    class Failed(api.Strategy):
        phase = "init"

        def init(self):
            self.x = self.ta.sma(length=2)
            captured.append(self)
            if self.phase == "init":
                raise RuntimeError("init failed")

        def next(self):
            raise RuntimeError("next failed")

    for phase in ["init", "next"]:
        with pytest.raises(RuntimeError, match=f"{phase} failed"):
            api.Backtest(frame(20), Failed).run(phase=phase)
        strategy = captured[-1]
        assert strategy._data._indicator_cache is None
        assert strategy._indicator_cursor.phase == "complete"
        assert len(strategy.x) == 20


@pytest.mark.parametrize("mode", ["default", "spawn"])
def test_real_optimization_indicator_cache(mode, tmp_path):
    probe = Path(__file__).with_name("indicator_spawn_probe.py")
    result = subprocess.run(
        [sys.executable, str(probe), mode, str(tmp_path / "calls")],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout.splitlines()[-1])
    assert report["backend_calls"] <= report["processes"] + 1
    assert report["allocations"] == 1
    assert report["active_children"] == 0
    assert "resource_tracker" not in result.stderr


def test_legacy_worker_payload_without_cache_token():
    data = frame(20)
    bt = api.Backtest(data, Repeated, end_policy="close_at_last_close")
    with SharedMemoryManager() as manager:
        result = api.Backtest._mp_task((bt, manager.df2shm(data), [{"threshold": 1}]))
    assert result[0]["# Trades"] == 1


def test_sambo_reuses_indicator_results_for_trading_parameters(monkeypatch):
    calls = []
    execute = indicators.execute

    def counted(*args):
        calls.append(1)
        return execute(*args)

    monkeypatch.setattr(indicators, "execute", counted)
    bt = api.Backtest(frame(30), Repeated, end_policy="close_at_last_close")
    bt.optimize(
        threshold=[1, 2, 3],
        method="sambo",
        max_tries=6,
        random_state=42,
        maximize="Equity Final [$]",
    )
    assert len(calls) == 1
    assert not hasattr(bt, "_indicator_cache")


def test_shared_columns_avoid_materialization_and_index_survives_mapping_close():
    data = frame(30)
    with SharedMemoryManager() as manager:
        descriptors = manager.df2shm(data)
        restored, handles = manager.shm2df(descriptors)
        index = restored.index
        for handle, (name, _, shape, dtype) in zip(handles, descriptors):
            memory = np.ndarray(shape, dtype=dtype.base, buffer=handle.buf)
            if name == "Close":
                assert np.shares_memory(memory, restored.Close.to_numpy())
                assert not restored.Close.to_numpy().flags.writeable
            else:
                if name == manager._DF_INDEX_COL:
                    assert not np.shares_memory(memory, index.to_numpy())
            del memory
        for handle in handles:
            handle.close()
    assert index.equals(data.index)


def test_partial_shared_mapping_failure_closes_already_opened_handles(monkeypatch):
    from openbacktesting.simulation import parallel

    original = parallel.SharedMemory
    opened = []
    with SharedMemoryManager() as manager:
        descriptors = manager.df2shm(frame())

        def open_mapping(*args, **kwargs):
            if len(opened) == 1:
                raise OSError("mapping failed")
            handle = original(*args, **kwargs)
            opened.append(handle)
            return handle

        monkeypatch.setattr(parallel, "SharedMemory", open_mapping)
        with pytest.raises(OSError, match="mapping failed"):
            manager.shm2df(descriptors)
        assert opened[0]._buf is None


def test_cleanup_failure_does_not_skip_other_owned_segments():
    from unittest.mock import Mock

    failed = Mock(_create=True, name="failed")
    failed.unlink.side_effect = OSError("unlink failed")
    intact = Mock(_create=True, name="intact")
    manager = SharedMemoryManager()
    manager._shms = [failed, intact]
    with pytest.warns(ResourceWarning), pytest.raises(OSError, match="unlink failed"):
        manager.__exit__()
    intact.close.assert_called_once()
    intact.unlink.assert_called_once()


@pytest.mark.parametrize("phase", ["allocation", "dispatch", "cache"])
def test_optimization_setup_errors_release_shared_segments_and_scope(monkeypatch, phase):
    from openbacktesting.parallel import SharedMemory
    from openbacktesting.simulation import core as backtest_module

    created = []
    original = SharedMemoryManager.SharedMemory

    def allocate(self, **kwargs):
        if phase == "allocation" and len(created) == 1:
            raise OSError("allocation failed")
        handle = original(self, **kwargs)
        if kwargs.get("create"):
            created.append(handle.name)
        return handle

    class InlinePool:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def imap(self, callback, payloads):
            if phase == "dispatch":
                raise OSError("dispatch failed")
            return map(callback, payloads)

    def failed_cache(*args):
        raise OSError("cache failed")

    monkeypatch.setattr(api, "Pool", InlinePool)
    monkeypatch.setattr(SharedMemoryManager, "SharedMemory", allocate)
    if phase == "cache":
        monkeypatch.setattr(backtest_module, "optimization_cache", failed_cache)
    with pytest.raises(OSError, match=phase + " failed"):
        api.Backtest(frame(20), Repeated).optimize(threshold=[1, 2])
    assert created and not indicators._OPTIMIZATION_CACHES
    for name in created:
        with pytest.raises(FileNotFoundError):
            SharedMemory(name=name, track=False)


def test_failed_thread_pool_joins_before_releasing_cache_scope(monkeypatch):
    """线程异常退出时，尚未进入缓存的在途任务也必须先结束。"""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event, local

    from openbacktesting.simulation import core as backtest_module

    waiting, release, exited = Event(), Event(), Event()
    context = local()
    original_task = api.Backtest._mp_task
    original = backtest_module.optimization_cache

    def identified_task(payload):
        context.threshold = payload[2][0]["threshold"]
        return original_task(payload)

    def delayed_cache(token, budget):
        if context.threshold == 2:
            waiting.set()
            assert release.wait(10)
        return original(token, budget)

    class Failing(Repeated):
        def init(self):
            if self.threshold == 1:
                assert waiting.wait(10)
                raise RuntimeError("first batch failed")
            super().init()

    class ObservedPool(ThreadPool):
        def __exit__(self, *args):
            super().__exit__(*args)
            exited.set()

    monkeypatch.setattr(api, "Pool", lambda: ObservedPool(2))
    monkeypatch.setattr(optimization, "_batch", lambda values: [[value] for value in values])
    monkeypatch.setattr(backtest_module, "optimization_cache", delayed_cache)
    monkeypatch.setattr(api.Backtest, "_mp_task", staticmethod(identified_task))
    with ThreadPoolExecutor(1) as executor:
        future = executor.submit(api.Backtest(frame(20), Failing).optimize, threshold=[1, 2])
        try:
            assert exited.wait(10)
            # Pool.__exit__不会等待ThreadPool的在途worker；拥有者仍须保持scope。
            with pytest.raises(TimeoutError):
                future.result(timeout=0.1)
            assert indicators._OPTIMIZATION_CACHES
        finally:
            release.set()
        with pytest.raises(RuntimeError, match="first batch failed"):
            future.result(timeout=10)
    assert not indicators._OPTIMIZATION_CACHES
