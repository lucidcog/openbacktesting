"""Isolated regression: a backtest must finish when fork inherits a progress lock left by an abnormally terminated process."""

import hashlib
import json
import multiprocessing as mp
import os

import pandas as pd
from tqdm.auto import tqdm

from openbacktesting import Backtest, Strategy
from openbacktesting.test import GOOG


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
    # Simulate worker termination while holding the shared progress lock; the OS does not release this semaphore automatically.
    os._exit(0)


def collect(context):
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=run_backtest, args=(sender,))
    process.start()
    sender.close()
    try:
        assert receiver.poll(5), "Child backtest blocked on the inherited progress lock"
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
    # The parent creates only a lock, without a progress bar or monitor thread; contaminated state remains local to this probe.
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
