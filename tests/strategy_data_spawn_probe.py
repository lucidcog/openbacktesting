"""真实 spawn 优化验证直接行情来源不会串运行。"""

import json
import multiprocessing as mp

import openbacktesting as api
import numpy as np
import pandas as pd
from test_indicator_catalog import catalog_data
from test_strategy_data import DataTrading


def main():
    api.Pool = lambda: mp.get_context("spawn").Pool(2)
    bt = api.Backtest(catalog_data(40), DataTrading, end_policy="close_at_last_close")
    old, oh = bt.optimize(period=[3, 5], direct=[False], return_heatmap=True)
    new, nh = bt.optimize(period=[3, 5], direct=[True], return_heatmap=True)
    np.testing.assert_array_equal(oh, nh)
    pd.testing.assert_frame_equal(old["_trades"], new["_trades"])
    owner = new["_strategy"]
    assert owner.saved is owner.close
    assert owner.saved._cursor is owner.average._cursor is owner._indicator_cursor
    print(json.dumps({"equivalent": True, "active_children": len(mp.active_children())}))


if __name__ == "__main__":
    main()
