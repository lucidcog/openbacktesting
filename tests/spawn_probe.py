"""在真实独立解释器中验证默认/显式 spawn 优化和异常资源回收。"""

import argparse
import json
import multiprocessing as mp

import openbacktesting as api
from openbacktesting._util import SharedMemory, SharedMemoryManager
from openbacktesting.test import GOOG
from openbacktesting.test._test import SmaCross
from test_modularization import assert_result


class FailingStrategy(api.Strategy):
    parameter = 0

    def init(self):
        raise ValueError("进程内预期失败")

    def next(self):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["default", "spawn"], required=True)
    args = parser.parse_args()
    if args.mode == "spawn":
        api.Pool = lambda: mp.get_context("spawn").Pool(processes=2)
    bt = api.Backtest(GOOG.iloc[:80], SmaCross, end_policy="close_at_last_close")
    sequential = {
        (fast, slow): bt.run(fast=fast, slow=slow) for fast in (3, 5) for slow in (10, 15)
    }
    stats, heatmap = bt.optimize(fast=[3, 5], slow=[10, 15], random_state=42, return_heatmap=True)
    assert_result(stats, sequential[heatmap.idxmax()])
    assert all(heatmap.loc[pair] == result["SQN"] for pair, result in sequential.items())

    created = []
    original = SharedMemoryManager.SharedMemory

    def record(self, **kwargs):
        segment = original(self, **kwargs)
        if kwargs.get("create"):
            created.append(segment.name)
        return segment

    SharedMemoryManager.SharedMemory = record
    try:
        failed = api.Backtest(GOOG.iloc[:20], FailingStrategy)
        try:
            failed.optimize(parameter=[1, 2], random_state=42)
        except ValueError as error:
            assert str(error) == "进程内预期失败"
        else:
            raise AssertionError("策略异常未传播")
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
    print(
        json.dumps(
            {
                "mode": args.mode,
                "exception_segments_released": len(created),
                "package": api.__file__,
                "status": "passed",
            }
        )
    )


if __name__ == "__main__":
    main()
