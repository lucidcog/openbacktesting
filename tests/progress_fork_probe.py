"""隔离验证：fork继承被异常退出进程遗留的进度锁时，回测仍须结束。"""

import hashlib
import json
import multiprocessing as mp
import os

import pandas as pd
from openbacktesting import Backtest, Strategy
from openbacktesting.test import GOOG
from tqdm.auto import tqdm


class Signals(Strategy):
    def init(self):
        self.average = self.ta.sma(length=2)

    def next(self):
        if len(self.data) == 3:
            self.buy(qty=1)


def run_backtest(connection):
    stats = Backtest(GOOG.iloc[:30], Signals, end_policy="close_at_last_close").run()
    connection.send(
        {
            "equity": hashlib.sha256(
                pd.util.hash_pandas_object(stats["_equity_curve"]).to_numpy().tobytes()
            ).hexdigest(),
            "trades": stats["# Trades"],
            "average": stats["_strategy"].average[-1],
        }
    )
    connection.close()


def abandon_progress_lock(connection):
    tqdm.get_lock().acquire()
    connection.send("held")
    # 模拟worker在持有共享进度锁时被终止；操作系统不会自动释放此信号量。
    os._exit(0)


def collect(context):
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=run_backtest, args=(sender,))
    process.start()
    sender.close()
    try:
        assert receiver.poll(5), "子进程回测被继承的进度锁阻塞"
        result = receiver.recv()
        process.join(5)
        assert process.exitcode == 0
        return result
    finally:
        if process.is_alive():
            process.kill()
            process.join(5)
        receiver.close()
        process.close()


def main():
    context = mp.get_context("fork")
    expected = collect(context)
    # 父进程只创建锁，不创建进度条或监视线程，污染状态局限于本探针。
    tqdm.get_lock()
    receiver, sender = context.Pipe(duplex=False)
    owner = context.Process(target=abandon_progress_lock, args=(sender,))
    owner.start()
    sender.close()
    try:
        assert receiver.poll(5) and receiver.recv() == "held"
        owner.join(5)
        assert owner.exitcode == 0
        actual = collect(context)
        assert actual == expected and actual["trades"] == 1, (actual, expected)
        print(json.dumps(actual))
    finally:
        if owner.is_alive():
            owner.kill()
            owner.join(5)
        receiver.close()
        owner.close()


if __name__ == "__main__":
    main()
