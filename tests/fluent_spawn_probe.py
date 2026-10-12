"""Compare named attributes and key access under spawn; independently verify serialization of named results and bound callbacks."""

import json
import multiprocessing as mp

import pandas as pd
from test_fluent_indicators import Trading
from test_indicator_catalog import catalog_data

import openbacktesting as api
from openbacktesting.indicators import runtime as indicators


def main():
    api.Pool = lambda: mp.get_context("spawn").Pool(2)
    bt = api.Backtest(catalog_data(150), Trading, end_policy="close_at_last_close")
    old, oh = bt.optimize(length=[5, 10], named_access=[False], return_heatmap=True)
    new, nh = bt.optimize(length=[5, 10], named_access=[True], return_heatmap=True)
    assert list(oh) == list(nh)
    pd.testing.assert_frame_equal(old["_trades"], new["_trades"])
    strategy = new["_strategy"]
    assert strategy.ta._register.__self__ is strategy
    assert strategy.histogram._cursor is strategy._indicator_cursor
    assert not indicators._OPTIMIZATION_CACHES
    print(json.dumps({"equivalent": True, "active_children": len(mp.active_children())}))


if __name__ == "__main__":
    main()
