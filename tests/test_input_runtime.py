"""输入在原生、标题、分数及并行运行中的绑定与隔离。"""

import multiprocessing as mp
import pickle
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.dummy import Pool as ThreadPool

import openbacktesting as api
import numpy as np
import pandas as pd
import pytest
from openbacktesting import Backtest, Strategy, inputs
from openbacktesting.broker import InstrumentSpec
from openbacktesting.parallel import SharedMemory, SharedMemoryManager
from openbacktesting.test import GOOG
from test_inputs import Mode, request


class TradingInputs(Strategy):
    units = inputs.int(1, minval=1, maxval=3, title="数量")
    mode = inputs.enum(Mode.FAST, title="模式")
    enabled = inputs.bool(True, title="启用")
    plain = 10

    def init(self):
        self.observed = (self.units, self.mode, self.enabled)

    def next(self):
        assert self.observed == (self.units, self.mode, self.enabled)
        assert type(self.mode) is Mode
        if len(self.data) == 2 and self.enabled:
            self.buy(qty=self.units)
        elif len(self.data) == 5:
            self.position.close()


class EmptyInputs(TradingInputs):
    def next(self):
        pass


class FailingInputs(TradingInputs):
    def init(self):
        raise ValueError("预期的输入策略错误")


@pytest.fixture
def data():
    return GOOG.iloc[:12]


def compare(a, b):
    pd.testing.assert_series_equal(
        a.filter(regex="^[^_]"),
        b.filter(regex="^[^_]"),
    )
    pd.testing.assert_frame_equal(a["_trades"], b["_trades"])
    pd.testing.assert_frame_equal(a["_equity_curve"], b["_equity_curve"])


def test_two_entry_points_and_full_snapshot(data):
    bt = Backtest(data, TradingInputs)
    native = bt.run(units=2, mode=Mode.SLOW)
    titled = bt.run_inputs(request(TradingInputs, {"数量": 2, "模式": "SLOW"}))
    compare(native, titled)
    assert native.attrs == titled.attrs
    assert titled["_strategy"].observed == (2, Mode.SLOW, True)
    snapshot = titled.attrs["input_snapshot"]
    assert snapshot["values"] == {"数量": 2, "模式": "SLOW", "启用": True}
    assert snapshot["overriddenTitles"] == ["数量", "模式"]
    assert snapshot["engineVersion"] == api.__version__
    assert titled["_strategy"]._params == {"units": 2, "mode": Mode.SLOW}
    rerun = bt.run_inputs({k: snapshot[k] for k in ("schemaVersion", "schemaHash", "values")})
    compare(titled, rerun)
    assert rerun.attrs["input_snapshot"]["overriddenTitles"] == ["数量", "模式", "启用"]
    default = bt.run()
    assert default["_strategy"].observed == (1, Mode.FAST, True)
    assert default.attrs["input_snapshot"]["overriddenTitles"] == []
    assert default["_strategy"]._params == {}
    assert TradingInputs.units.default == 1
    assert native["Return [%]"] != default["Return [%]"]
    snapshot["values"]["数量"] = 99
    assert native.attrs["input_snapshot"]["values"]["数量"] == 2
    assert bt.run()["_strategy"].units == 1
    restored = pickle.loads(pickle.dumps(titled["_strategy"]))
    assert restored.units == 2 and restored.mode is Mode.SLOW


def test_invalid_inputs_precede_all_execution(data, monkeypatch):
    bt = Backtest(data, TradingInputs)
    last = bt.run()

    def fail(*args, **kwargs):
        raise AssertionError("不应执行")

    monkeypatch.setattr(bt, "_broker", fail)
    monkeypatch.setattr(TradingInputs, "__init__", fail)
    for call in [
        lambda: bt.run(units=True),
        lambda: bt.run(plain=1),
        lambda: bt.run_inputs(request(TradingInputs, {"units": 2})),
        lambda: bt.run_inputs(request(TradingInputs, {"数量": "2"})),
        lambda: bt.run_inputs(request(TradingInputs, {}) | {"schemaHash": "old"}),
    ]:
        with pytest.raises(inputs.InputError):
            call()
        assert bt._results is last


@pytest.mark.parametrize("phase", ["init", "next"])
@pytest.mark.parametrize("remove", [False, True])
def test_input_is_readonly_in_lifecycle(data, phase, remove):
    def mutate(self):
        if remove:
            del self.units
        else:
            self.units = 2

    cls = type("Mutating", (TradingInputs,), {phase: mutate})
    with pytest.raises(inputs.InputError, match="ImmutableInput"):
        Backtest(data, cls).run()


def test_fractional_and_custom_run_dispatch(data):
    class FractionalInputs(TradingInputs):
        def next(self):
            if len(self.data) == 2 and self.enabled:
                self.buy(qty=self.units / 10)
            elif len(self.data) == 5:
                self.close_position()

    class ObservedFractional(Backtest):
        def run(self, **kwargs):
            self.calls = getattr(self, "calls", 0) + 1
            return super().run(**kwargs)

    bt = ObservedFractional(data, FractionalInputs, instrument=InstrumentSpec(quantity_step=0.1))
    native = bt.run(units=2)
    titled = bt.run_inputs(request(FractionalInputs, {"数量": 2}))
    compare(native, titled)
    assert bt.calls == 2
    assert titled["_trades"]["Size"].iloc[0] == 0.2
    assert titled["_trades"]["EntryPrice"].iloc[0] == data.Open.iloc[2]


def test_separate_instances_across_threads(data):
    def execute(n):
        return Backtest(data, TradingInputs).run(units=n)["_strategy"].observed

    with ThreadPoolExecutor(max_workers=3) as pool:
        observed = list(pool.map(execute, [1, 2, 3, 2, 1]))
    assert observed == [(n, Mode.FAST, True) for n in [1, 2, 3, 2, 1]]


def test_grid_validates_before_constraints_and_dispatch(data, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("不可派发或调用 constraint")

    monkeypatch.setattr(api, "Pool", fail)
    bt = Backtest(data, TradingInputs)
    for values in [[1, 0], [2, True], [2, 4]]:
        with pytest.raises(inputs.InputError):
            bt.optimize(units=values, constraint=fail, max_tries=0.01)
    with pytest.raises(inputs.InputError, match="UnknownInput"):
        bt.optimize(plain=[1])
    for method in ["sambo", "skopt"]:
        with pytest.raises(inputs.InputError, match="UnsupportedOptimizationInput"):
            bt.optimize(units=[1], method=method)


@pytest.mark.parametrize("pool_mode", ["thread", "default", "spawn"])
def test_grid_values_best_result_and_process_cleanup(data, monkeypatch, pool_mode):
    if pool_mode == "thread":
        monkeypatch.setattr(api, "Pool", lambda: ThreadPool(2))
    elif pool_mode == "spawn":
        monkeypatch.setattr(api, "Pool", lambda: mp.get_context("spawn").Pool(2))
    created = []
    original = SharedMemoryManager.SharedMemory

    def record(self, **kwargs):
        segment = original(self, **kwargs)
        if kwargs.get("create"):
            created.append(segment.name)
        return segment

    monkeypatch.setattr(SharedMemoryManager, "SharedMemory", record)
    seen = []

    def constraint(p):
        assert type(p.mode) is Mode and type(p.units) is int
        seen.append(p.units)
        return True

    bt = Backtest(data, TradingInputs)
    best, heatmap = bt.optimize(
        units=[np.int64(1), np.int64(2)],
        mode=[Mode.FAST, Mode.SLOW],
        constraint=constraint,
        maximize="Return [%]",
        return_heatmap=True,
        random_state=1,
    )
    assert seen and len(heatmap) == 4
    assert heatmap.index.names == ["units", "mode"]
    assert best.attrs["input_snapshot"]["values"]["数量"] in (1, 2)
    assert best.attrs["input_snapshot"]["values"]["模式"] in ("FAST", "SLOW")
    compare(best, bt.run(**best["_strategy"]._params))
    empty = Backtest(data, EmptyInputs).optimize(units=[1, 2], enabled=[True, False])
    assert empty["# Trades"] == 0
    assert "input_snapshot" in empty.attrs
    with pytest.raises(ValueError, match="预期的输入策略错误"):
        Backtest(data, FailingInputs).optimize(units=[1, 2])
    assert created
    for name in created:
        with pytest.raises(FileNotFoundError):
            SharedMemory(name=name, track=False)


def test_workers_stop_before_shared_memory_release(data, monkeypatch):
    created = []
    original = SharedMemoryManager.SharedMemory

    def record(self, **kwargs):
        segment = original(self, **kwargs)
        if kwargs.get("create"):
            created.append(segment.name)
        return segment

    class InspectPool:
        def __enter__(self):
            self.pool = ThreadPool(2)
            return self.pool

        def __exit__(self, *exc):
            # 即使任务抛异常，退出池时数据仍须有效，避免运行中或待派发任务访问已释放段。
            try:
                assert created
                for name in tuple(created):
                    segment = SharedMemory(name=name, track=False)
                    segment.close()
            finally:
                self.pool.__exit__(*exc)

    monkeypatch.setattr(api, "Pool", InspectPool)
    monkeypatch.setattr(SharedMemoryManager, "SharedMemory", record)
    with pytest.raises(ValueError, match="预期的输入策略错误"):
        Backtest(data, FailingInputs).optimize(units=[1, 2, 3])
    for name in created:
        with pytest.raises(FileNotFoundError):
            SharedMemory(name=name, track=False)


def test_thread_batches_do_not_share_backtest_state(data, monkeypatch):
    instances = []

    class ObservedBacktest(Backtest):
        def run(self, **kwargs):
            instances.append(self)
            return super().run(**kwargs)

    monkeypatch.setattr(api, "Pool", lambda: ThreadPool(2))
    bt = ObservedBacktest(data, TradingInputs)
    result = bt.optimize(units=[1, 2, 3])
    # 三个批次及最佳参数重跑；保留实例引用，避免对象回收后 id 重用。
    assert len({id(instance) for instance in instances}) == 4
    assert instances[-1] is bt
    for instance in instances:
        state = instance._results["_strategy"]
        assert instance._results.attrs["input_snapshot"]["values"]["数量"] == state.units
    assert result is bt._results
