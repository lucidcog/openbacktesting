"""原生参数搜索与并行优化编排。"""

from __future__ import annotations

import warnings
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from copy import copy
from functools import lru_cache
from itertools import product, repeat
from multiprocessing.pool import ThreadPool

import numpy as np
import pandas as pd
from numpy.random import default_rng

from openbacktesting.helpers import patch
from openbacktesting.indicators.runtime import (
    DEFAULT_CACHE_BYTES,
    IndicatorCache,
    optimization_scope,
)
from openbacktesting.portfolio.stats import dummy_stats
from openbacktesting.simulation.parallel import SharedMemoryManager, _batch
from openbacktesting.strategy.inputs import InputError, _definitions, request_for, resolve_native
from openbacktesting.util import _tqdm


@contextmanager
def _joined_pool(pool):
    """ThreadPool.__exit__不等待在途线程；先回收再释放行情与缓存。"""
    active = pool
    try:
        with pool as active:
            yield active
    finally:
        if isinstance(active, ThreadPool):
            active.join()


def _optimize(
    self,
    _mp_task,
    *,
    maximize: str | Callable[[pd.Series], float] = "SQN",
    method: str = "grid",
    max_tries: float | None = None,
    constraint: Callable[[dict], bool] | None = None,
    return_heatmap: bool = False,
    return_optimization: bool = False,
    random_state: int | None = None,
    **kwargs,
) -> pd.Series | tuple[pd.Series, pd.Series] | tuple[pd.Series, pd.Series, dict]:
    if not kwargs:
        raise ValueError("Need some strategy parameters to optimize")

    declarations = _definitions(self._strategy)
    if not declarations:
        self._strategy._check_reserved_params(kwargs)
    if declarations and method in ("sambo", "skopt"):
        raise InputError("UnsupportedOptimizationInput", None, "声明策略首期仅支持 grid")

    maximize_key = None
    if isinstance(maximize, str):
        maximize_key = str(maximize)
        if maximize not in dummy_stats().index:
            raise ValueError(
                "`maximize`, if str, must match a key in pd.Series result of backtest.run()"
            )

        def maximize(stats: pd.Series, _key=maximize):
            return stats[_key]

    elif not callable(maximize):
        raise TypeError(
            "`maximize` must be str (a field of backtest.run() result "
            "Series) or a function that accepts result Series "
            "and returns a number; the higher the better"
        )
    assert callable(maximize), maximize

    have_constraint = bool(constraint)
    if constraint is None:

        def constraint(_):
            return True

    elif not callable(constraint):
        raise TypeError(
            "`constraint` must be a function that accepts a dict "
            "of strategy parameters and returns a bool whether "
            "the combination of parameters is admissible or not"
        )
    assert callable(constraint), constraint

    if method == "skopt":
        method = "sambo"
        warnings.warn(
            '`Backtest.optimize(method="skopt")` is deprecated. Use `method="sambo"`.',
            DeprecationWarning,
            stacklevel=2,
        )
    if return_optimization and method != "sambo":
        raise ValueError("return_optimization=True only valid if method='sambo'")

    def _tuple(x):
        return x if isinstance(x, Sequence) and not isinstance(x, str) else (x,)

    for k, v in kwargs.items():
        if len(_tuple(v)) == 0:
            raise ValueError(
                f"Optimization variable '{k}' is passed no optimization values: {k}={v}"
            )

    if declarations:
        # 在 constraint 与随机采样之前验证所有值，不能隐藏非法候选。
        kwargs = {
            name: [
                resolve_native(self._strategy, {name: value}).overrides()[name]
                for value in _tuple(values)
            ]
            for name, values in kwargs.items()
        }

    class AttrDict(dict):
        def __getattr__(self, item):
            return self[item]

    def _grid_size():
        size = int(np.prod([len(_tuple(v)) for v in kwargs.values()]))
        if size < 10_000 and have_constraint:
            size = sum(
                1
                for p in product(*(zip(repeat(k), _tuple(v)) for k, v in kwargs.items()))
                if constraint(AttrDict(p))
            )
        return size

    def _optimize_grid() -> pd.Series | tuple[pd.Series, pd.Series]:
        rand = default_rng(random_state).random
        grid_frac = (
            1
            if max_tries is None
            else max_tries
            if 0 < max_tries <= 1
            else max_tries / _grid_size()
        )
        param_combos = [
            dict(params)  # back to dict so it pickles
            for params in (
                AttrDict(params)
                for params in product(*(zip(repeat(k), _tuple(v)) for k, v in kwargs.items()))
            )
            if constraint(params) and rand() <= grid_frac
        ]
        if not param_combos:
            raise ValueError("No admissible parameter combinations to test")

        if len(param_combos) > 300:
            warnings.warn(
                f"Searching for best of {len(param_combos)} configurations.", stacklevel=2
            )

        heatmap = pd.Series(
            np.nan,
            name=maximize_key,
            index=pd.MultiIndex.from_tuples(
                [p.values() for p in param_combos], names=next(iter(param_combos)).keys()
            ),
        )

        batches = list(_batch(param_combos))
        if declarations:
            batches = [
                [request_for(self._strategy, params) for params in batch] for batch in batches
            ]

        from openbacktesting import Pool

        with (
            optimization_scope(
                getattr(self, "_indicator_cache_bytes", DEFAULT_CACHE_BYTES)
            ) as token,
            SharedMemoryManager() as smm,
            _joined_pool(Pool()) as pool,
        ):
            with patch(self, "_data", None):
                bt = copy(self)  # bt._data will be reassigned in _mp_task worker
            bt._portfolio_enabled = maximize_key is None
            bt._results = None
            bt._log_collector = None
            bt._indicator_cache_token = token
            data_shm = smm.df2shm(self._data)
            results = _tqdm(
                pool.imap(
                    _mp_task,
                    ((bt, data_shm, params_batch) for params_batch in batches),
                ),
                total=len(param_combos),
                desc="Backtest.optimize",
            )
            for param_batch, result in zip(_batch(param_combos), results):
                for params, stats in zip(param_batch, result):
                    if stats is not None:
                        heatmap[tuple(params.values())] = maximize(stats)

        if pd.isnull(heatmap).all():
            # No trade was made in any of the runs. Just make a random
            # run so we get some, if empty, results
            stats = self.run(**param_combos[0])
        else:
            best_params = heatmap.idxmax(skipna=True)
            stats = self.run(**dict(zip(heatmap.index.names, best_params)))

        if return_heatmap:
            return stats, heatmap
        return stats

    def _optimize_sambo() -> (
        pd.Series | tuple[pd.Series, pd.Series] | tuple[pd.Series, pd.Series, dict]
    ):
        try:
            import sambo
        except ImportError:
            raise ImportError(
                "Need package 'sambo' for method='sambo'. pip install sambo"
            ) from None

        nonlocal max_tries
        max_tries = (
            200
            if max_tries is None
            else max(1, int(max_tries * _grid_size()))
            if 0 < max_tries <= 1
            else max_tries
        )

        dimensions = []
        for values in kwargs.values():
            values = np.asarray(values)
            if values.dtype.kind in "mM":  # timedelta, datetime64
                # these dtypes are unsupported in SAMBO, so convert to raw int
                # TODO: save dtype and convert back later
                values = values.astype(np.int64)

            if values.dtype.kind in "iumM":
                dimensions.append((values.min(), values.max() + 1))
            elif values.dtype.kind == "f":
                dimensions.append((values.min(), values.max()))
            else:
                dimensions.append(values.tolist())

        # Avoid recomputing re-evaluations
        @lru_cache
        def memoized_run(tup):
            nonlocal maximize, self
            with (
                patch(self, "_plotting_enabled", False),
                patch(self, "_logs_enabled", False),
                patch(self, "_portfolio_enabled", maximize_key is None),
            ):
                stats = self.run(**dict(tup))
            return -maximize(stats)

        progress = iter(
            _tqdm(
                repeat(None),
                total=max_tries,
                leave=False,
                desc=self.optimize.__qualname__,
                mininterval=2,
            )
        )
        _names = tuple(kwargs.keys())

        def objective_function(x):
            nonlocal progress, memoized_run, constraint, _names
            next(progress)
            value = memoized_run(tuple(zip(_names, x)))
            return 0 if np.isnan(value) else value

        def cons(x):
            nonlocal constraint, _names
            return constraint(AttrDict(zip(_names, x)))

        res = sambo.minimize(
            fun=objective_function,
            bounds=dimensions,
            constraints=cons,
            max_iter=max_tries,
            method="sceua",
            rng=random_state,
        )

        stats = self.run(**dict(zip(kwargs.keys(), res.x)))
        output = [stats]

        if return_heatmap:
            heatmap = pd.Series(dict(zip(map(tuple, res.xv), -res.funv)), name=maximize_key)
            heatmap.index.names = kwargs.keys()
            heatmap.sort_index(inplace=True)
            output.append(heatmap)

        if return_optimization:
            output.append(res)

        return stats if len(output) == 1 else tuple(output)

    if method == "grid":
        output = _optimize_grid()
    elif method in ("sambo", "skopt"):
        with patch(
            self,
            "_indicator_cache",
            IndicatorCache(getattr(self, "_indicator_cache_bytes", DEFAULT_CACHE_BYTES)),
        ):
            output = _optimize_sambo()
    else:
        raise ValueError(f"Method should be 'grid' or 'sambo', not {method!r}")
    return output


from openbacktesting.helpers import _set_legacy_module

_set_legacy_module(_joined_pool, "openbacktesting.optimization")
_set_legacy_module(_optimize, "openbacktesting.optimization")
