"""Strategy helpers for event predicates, statistics, and resampling."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from inspect import currentframe
from itertools import compress

import numpy as np
import pandas as pd

from openbacktesting.data.aggregation import OHLCV_AGG
from openbacktesting.data.core import _Array
from openbacktesting.helpers import _as_str, _set_legacy_module
from openbacktesting.indicators.types import IndicatorHandle
from openbacktesting.strategy.base import Strategy


def barssince(condition: Sequence[bool], default=np.inf) -> int:
    """Query the distance from the current position to the latest true condition; this is a scalar helper.


    Return the number of bars since `condition` sequence was last `True`,
    or if never, return `default`.

        >>> barssince(self.data.Close > self.data.Open)
        3
    """
    return next(compress(range(len(condition)), reversed(condition)), default)


def quantile(series: Sequence, quantile: None | float = None):
    """Query the relative rank of the last value or a specified quantile value, depending on quantile.


    If `quantile` is `None`, return the quantile _rank_ of the last
    value of `series` wrt former series values.

    If `quantile` is a value between 0 and 1, return the _value_ of
    `series` at this quantile. If used to working with percentiles, just
    divide your percentile amount with 100 to obtain quantiles.

        >>> quantile(self.data.Close[-20:], .1)
        162.130
        >>> quantile(self.data.Close)
        0.13
    """
    if quantile is None:
        try:
            last, series = series[-1], series[:-1]
            return np.mean(series < last)
        except IndexError:
            return np.nan
    assert 0 <= quantile <= 1, "quantile must be within [0, 1]"
    return np.nanpercentile(series, quantile * 100)


def resample_apply(
    rule: str,
    func: Callable[..., Sequence] | None,
    series: pd.Series | pd.DataFrame | _Array,
    *args,
    agg: str | dict | None = None,
    **kwargs,
):
    """Resample and apply the function, then align to the original calendar; automatically register the result handle within strategy initialization.


    Apply `func` (such as an indicator) to `series`, resampled to
    a time frame specified by `rule`. When called from inside
    `openbacktesting.engine.Strategy.init`,
    the result (returned) series will be automatically wrapped in
    `openbacktesting.engine.Strategy.ind`
    wrapper method.

    `rule` is a valid [Pandas offset string] indicating
    a time frame to resample `series` to.

    [Pandas offset string]: \
http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

    `func` is the indicator function to apply on the resampled series.

    `series` is a data series (or array), such as any of the
    `openbacktesting.engine.Strategy.data` series. Due to pandas
    resampling limitations, this only works when input series
    has a datetime index.

    `agg` is the aggregation function to use on resampled groups of data.
    Valid values are anything accepted by `pandas/resample/.agg()`.
    Default value for dataframe input is `OHLCV_AGG` dictionary.
    Default value for series input is the appropriate entry from `OHLCV_AGG`
    if series has a matching name, or otherwise the value `"last"`,
    which is suitable for closing prices,
    but you might prefer another (e.g. `"max"` for peaks, or similar).

    Finally, any `*args` and `**kwargs` that are not already eaten by
    implicit `openbacktesting.engine.Strategy.ind` call
    are passed to `func`.

    For example, if we have a typical moving average function
    `SMA(values, lookback_period)`, _hourly_ data source, and need to
    apply the moving average MA(10) on a _daily_ time frame, we can do::

        class System(Strategy):
            def init(self):
                self.sma = resample_apply(
                    'D', SMA, self.data.Close, 10)

    The above short snippet is roughly equivalent to::

        class System(Strategy):
            def init(self):
                # Strategy exposes `self.data` as raw NumPy arrays.
                # Let's convert closing prices back to pandas Series.
                close = self.data.Close.s

                # Resample to daily resolution. Aggregate groups
                # using their last value (i.e. closing price at the end
                # of the day). Notice `label='right'`. If it were set to
                # 'left' (default), the strategy would exhibit
                # look-ahead bias.
                daily = close.resample('D', label='right').agg('last')

                # We apply SMA(10) to daily close prices,
                # then reindex it back to original hourly index,
                # forward-filling the missing values in each day.
                # We make a separate function that returns the final
                # indicator array.
                def SMA(series, n):
                    from openbacktesting.test import SMA
                    return SMA(series, n).reindex(close.index).ffill()

                # The result equivalent to the short example above:
                self.sma = self.ind(SMA, daily, 10)

    """
    if func is None:

        def func(x, *_, **__):
            return x

    assert callable(func), "resample_apply(func=) must be callable"

    if not isinstance(series, (pd.Series, pd.DataFrame)):
        assert isinstance(series, (_Array, IndicatorHandle)), (
            "resample_apply(series=) must be `pd.Series`, `pd.DataFrame`, "
            "or a `Strategy.data.*` array"
        )
        series = series.s

    if agg is None:
        agg = OHLCV_AGG.get(getattr(series, "name", ""), "last")
        if isinstance(series, pd.DataFrame):
            agg = {column: OHLCV_AGG.get(column, "last") for column in series.columns}

    resampled = series.resample(rule, label="right").agg(agg).dropna()
    resampled.name = _as_str(series) + "[" + rule + "]"

    # Check first few stack frames if we are being called from
    # inside Strategy.init, and if so, extract Strategy.ind wrapper.
    frame, level = currentframe(), 0
    while frame and level <= 3:
        frame = frame.f_back
        level += 1
        if isinstance(frame.f_locals.get("self"), Strategy):  # type: ignore
            strategy_ind = frame.f_locals["self"].ind  # type: ignore
            break
    else:

        def strategy_ind(func, *args, **kwargs):
            return func(*args, **kwargs)

    def wrap_func(resampled, *args, **kwargs):
        result = func(resampled, *args, **kwargs)
        if not isinstance(result, pd.DataFrame) and not isinstance(result, pd.Series):
            result = np.asarray(result)
            if result.ndim == 1:
                result = pd.Series(result, name=resampled.name)
            elif result.ndim == 2:
                result = pd.DataFrame(result.T)
        # Resample back to data index
        if not isinstance(result.index, pd.DatetimeIndex):
            result.index = resampled.index
        result = result.reindex(index=series.index.union(resampled.index), method="ffill").reindex(
            series.index
        )
        return result

    wrap_func.__name__ = func.__name__

    array = strategy_ind(wrap_func, resampled, *args, **kwargs)
    return array


_set_legacy_module(barssince, "openbacktesting.lib")
_set_legacy_module(quantile, "openbacktesting.lib")
_set_legacy_module(resample_apply, "openbacktesting.lib")
