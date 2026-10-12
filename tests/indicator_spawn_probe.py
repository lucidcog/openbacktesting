"""真实默认线程/显式 spawn 验证，计数文件仅记录本次测试的后端调用。"""

import json
import multiprocessing as mp
import os
import sys
from collections import Counter
from pathlib import Path

import openbacktesting as api
from openbacktesting import optimization
from openbacktesting.indicators import runtime as indicators
from openbacktesting.parallel import SharedMemoryManager
from test_indicator_optimization import Repeated
from test_indicator_regressions import frame

_execute = indicators.execute


def counted(*args):
    path = os.environ.get("OPENBACKTESTING_INDICATOR_CALLS")
    if path:
        with open(path, "a") as stream:
            stream.write(f"{os.getpid()}\n")
    return _execute(*args)


indicators.execute = counted


def main():
    mode, path = sys.argv[1:]
    os.environ["OPENBACKTESTING_INDICATOR_CALLS"] = path
    if mode == "spawn":
        api.Pool = lambda: mp.get_context("spawn").Pool(2)
    optimization._batch = lambda values: [[value] for value in values]
    allocations = []
    original = SharedMemoryManager.df2shm

    def allocate(self, data):
        allocations.append(1)
        return original(self, data)

    SharedMemoryManager.df2shm = allocate
    result = api.Backtest(frame(100), Repeated, end_policy="close_at_last_close").optimize(
        threshold=list(range(8)), maximize="Equity Final [$]"
    )
    assert result["_strategy"].calls == 100
    assert result["_strategy"]._bar_context is None
    assert result.attrs["statistics_initial_equity"] == 10000
    calls = Counter(Path(path).read_text().splitlines())
    assert not indicators._OPTIMIZATION_CACHES
    assert all(count == 1 for pid, count in calls.items() if pid != str(os.getpid()))
    print(
        json.dumps(
            {
                "backend_calls": sum(calls.values()),
                "processes": len(calls),
                "allocations": len(allocations),
                "active_children": len(mp.active_children()),
            }
        )
    )


if __name__ == "__main__":
    main()
