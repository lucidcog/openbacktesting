"""独立进程记录交易事实表规模、耗时与峰值RSS，不设无依据性能阈值。"""

import argparse
import json
import resource
import sys
import time

import pandas as pd
from openbacktesting import Backtest, Strategy


class Cycles(Strategy):
    def init(self):
        pass

    def next(self):
        bar = len(self.data) - 1
        if bar % 1000 == 1:
            self.buy(qty=1)
        elif bar % 1000 == 2:
            self.close_position()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bars", type=int, default=100_000)
    args = parser.parse_args()
    frame = pd.DataFrame(
        {"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0},
        index=pd.date_range("2026-01-01", periods=args.bars, freq="min", tz="UTC"),
    )
    start = time.perf_counter()
    result = Backtest(frame, Cycles).run()
    elapsed = time.perf_counter() - start
    names = (
        "_orders",
        "_order_events",
        "_fills",
        "_trade_allocations",
        "_positions",
        "_account_curve",
    )
    rows = {name: len(result[name]) for name in names}
    assert rows["_positions"] == rows["_account_curve"] == args.bars + 1
    assert rows["_orders"] == rows["_fills"] == rows["_trade_allocations"] == args.bars // 1000 * 2
    assert rows["_order_events"] == rows["_orders"] * 3
    assert result._final_account["equity"] == 10000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(
        json.dumps(
            {
                "bars": args.bars,
                "seconds": elapsed,
                "peak_rss_bytes": rss if sys.platform == "darwin" else rss * 1024,
                "rows": rows,
                "platform": sys.platform,
                "status": "passed",
            }
        )
    )


if __name__ == "__main__":
    main()
