"""从 lib 迁入的既有实现：FractionalBacktest, MultiBacktest。"""

from __future__ import annotations

from itertools import chain, count

import pandas as pd

from openbacktesting.helpers import _set_legacy_module
from openbacktesting.simulation.core import Backtest
from openbacktesting.simulation.parallel import SharedMemoryManager, _batch
from openbacktesting.util import _tqdm


class FractionalBacktest(Backtest):
    """已移除的价格缩放入口；请使用Backtest与InstrumentSpec。"""

    def __init__(self, *args, **kwargs):
        raise TypeError(
            "FractionalBacktest已移除；使用Backtest(instrument=InstrumentSpec(quantity_step=...))及qty"
        )


class MultiBacktest:
    """在多个数据集上运行同一策略，汇总各数据集统计。


    Multi-dataset `openbacktesting.engine.Backtest` wrapper.

    Run supplied `openbacktesting.engine.Strategy` on several instruments,
    in parallel.  Used for comparing strategy runs across many instruments
    or classes of instruments. Example:

        from openbacktesting.test import EURUSD, BTCUSD, SmaCross
        btm = MultiBacktest([EURUSD, BTCUSD], SmaCross)
        stats_per_ticker: pd.DataFrame = btm.run(fast=10, slow=20)
        heatmap_per_ticker: pd.DataFrame = btm.optimize(...)
    """

    def __init__(self, df_list, strategy_cls, **kwargs):
        self._dfs = df_list
        self._strategy = strategy_cls
        self._bt_kwargs = kwargs

    def run(self, **kwargs):
        """在每份数据上执行回测，并按数据集列返回统计表。


        Wraps `openbacktesting.engine.Backtest.run`. Returns `pd.DataFrame` with
        currency indexes in columns.
        """
        from openbacktesting import Pool

        with Pool() as pool, SharedMemoryManager() as smm:
            shm = [smm.df2shm(df) for df in self._dfs]
            results = _tqdm(
                pool.imap(
                    self._mp_task_run,
                    (
                        (df_batch, self._strategy, self._bt_kwargs, kwargs)
                        for df_batch in _batch(shm)
                    ),
                ),
                total=len(shm),
                desc=self.run.__qualname__,
                mininterval=2,
            )
            df = pd.DataFrame(list(chain(*results))).transpose()
        return df

    @staticmethod
    def _mp_task_run(args):
        data_shm, strategy, bt_kwargs, run_kwargs = args
        dfs, shms = zip(*(SharedMemoryManager.shm2df(i) for i in data_shm))
        try:
            return [
                stats.filter(regex="^[^_]")
                for stats in (Backtest(df, strategy, **bt_kwargs).run(**run_kwargs) for df in dfs)
            ]
        finally:
            for shmem in chain(*shms):
                shmem.close()

    def optimize(self, **kwargs) -> pd.DataFrame:
        """分别优化各数据集的参数，汇总参数评分结果。


        Wraps `openbacktesting.engine.Backtest.optimize`, but returns `pd.DataFrame` with
        currency indexes in columns.

            heatmap: pd.DataFrame = btm.optimize(...)
            mean_scores = heatmap.mean(axis=1)
        """
        heatmaps = []
        # Simple loop since bt.optimize already does its own multiprocessing
        for df in _tqdm(self._dfs, desc=self.__class__.__name__, mininterval=2):
            bt = Backtest(df, self._strategy, **self._bt_kwargs)
            _best_stats, heatmap = bt.optimize(  # type: ignore
                return_heatmap=True, return_optimization=False, **kwargs
            )
            heatmaps.append(heatmap)
        heatmap = pd.DataFrame(dict(zip(count(), heatmaps)))
        return heatmap


_set_legacy_module(FractionalBacktest, "openbacktesting.lib")
_set_legacy_module(MultiBacktest, "openbacktesting.lib")
