"""原生行情视图、指标数组及预热辅助函数。"""

from __future__ import annotations

import warnings
from numbers import Number
from typing import cast

import numpy as np
import pandas as pd

from openbacktesting.helpers import _set_legacy_module


def _data_period(index) -> pd.Timedelta | Number:
    """Return data index period as pd.Timedelta"""
    values = pd.Series(index[-100:])
    return values.diff().dropna().median()


def _strategy_indicators(strategy):
    return {
        attr: indicator
        for attr, indicator in strategy.__dict__.items()
        if isinstance(indicator, _Indicator)
    }.items()


def _indicator_warmup_nbars(strategy):
    """旧入口的指标就绪诊断；不再控制 next 调度或收益基准。"""
    if strategy is None:
        return 0
    if hasattr(strategy, "_indicator_cursor"):
        return max((indicator.first_ready() for indicator in strategy._indicators), default=0)
    nbars = max(
        (
            np.isnan(indicator.astype(float)).argmin(axis=-1).max()
            for _, indicator in _strategy_indicators(strategy)
            if indicator._opts.get("warmup", True)
        ),
        default=0,
    )
    return nbars


class _Array(np.ndarray):
    """
    ndarray extended to supply .name and other arbitrary properties
    in ._opts dict.
    """

    def __new__(cls, array, *, name=None, **kwargs):
        obj = np.asarray(array).view(cls)
        obj.name = name or array.name
        obj._opts = kwargs
        return obj

    def __array_finalize__(self, obj):
        if obj is not None:
            self.name = getattr(obj, "name", "")
            self._opts = getattr(obj, "_opts", {})

    # Make sure properties name and _opts are carried over
    # when (un-)pickling.
    def __reduce__(self):
        value = super().__reduce__()
        return value[:2] + (value[2] + (self.__dict__,),)

    def __setstate__(self, state):
        self.__dict__.update(state[-1])
        super().__setstate__(state[:-1])

    def __bool__(self):
        try:
            return bool(self[-1])
        except IndexError:
            return super().__bool__()

    def __float__(self):
        try:
            return float(self[-1])
        except IndexError:
            return super().__float__()

    def to_series(self):
        warnings.warn("`.to_series()` is deprecated. For pd.Series conversion, use accessor `.s`")
        return self.s

    @property
    def s(self) -> pd.Series:
        values = np.atleast_2d(self)
        index = self._opts["index"][: values.shape[1]]
        return pd.Series(values[0], index=index, name=self.name)

    @property
    def df(self) -> pd.DataFrame:
        values = np.atleast_2d(np.asarray(self))
        index = self._opts["index"][: values.shape[1]]
        df = pd.DataFrame(values.T, index=index, columns=[self.name] * len(values))
        return df


class _Indicator(_Array):
    pass


class _Data:
    """
    A data array accessor. Provides access to OHLCV "columns"
    as a standard `pd.DataFrame` would, except it's not a DataFrame
    and the returned "series" are _not_ `pd.Series` but `np.ndarray`
    for performance reasons.
    """

    def __init__(self, df: pd.DataFrame):
        self.__df = df
        self.__len = len(df)  # Current length
        self.__pip: float | None = None
        self.__cache: dict[str, _Array] = {}
        self.__arrays: dict[str, _Array] = {}
        self._update()

    def __getitem__(self, item):
        return self.__get_array(item)

    def __getattr__(self, item):
        try:
            return self.__get_array(item)
        except KeyError:
            raise AttributeError(f"Column '{item}' not in data") from None

    def _set_length(self, length):
        self.__len = length
        self.__cache.clear()

    def _update(self):
        index = self.__df.index.copy()
        self.__arrays = {col: _Array(arr, index=index) for col, arr in self.__df.items()}
        # Leave index as Series because pd.Timestamp nicer API to work with
        self.__arrays["__index"] = index

    def __repr__(self):
        i = min(self.__len, len(self.__df)) - 1
        index = self.__arrays["__index"][i]
        items = ", ".join(f"{k}={v}" for k, v in self.__df.iloc[i].items())
        return f"<Data i={i} ({index}) {items}>"

    def __len__(self):
        return self.__len

    @property
    def df(self) -> pd.DataFrame:
        return self.__df.iloc[: self.__len] if self.__len < len(self.__df) else self.__df

    def _full_frame(self) -> pd.DataFrame:
        """供内部来源捕获使用，不改变公开数据的可见长度。"""
        return self.__df

    @property
    def pip(self) -> float:
        if self.__pip is None:
            self.__pip = float(
                10
                ** -np.median(
                    [len(s.partition(".")[-1]) for s in self.__arrays["Close"].astype(str)]
                )
            )
        return self.__pip

    def __get_array(self, key) -> _Array:
        arr = self.__cache.get(key)
        if arr is None:
            arr = self.__cache[key] = cast(_Array, self.__arrays[key][: self.__len])
        return arr

    def _current_value(self, key: str):
        # Known fast path to avoid needless __get_array reslicing
        assert self.__len >= 0, self
        return self.__arrays[key][self.__len - 1]

    @property
    def Open(self) -> _Array:
        return self.__get_array("Open")

    @property
    def High(self) -> _Array:
        return self.__get_array("High")

    @property
    def Low(self) -> _Array:
        return self.__get_array("Low")

    @property
    def Close(self) -> _Array:
        return self.__get_array("Close")

    @property
    def Volume(self) -> _Array:
        return self.__get_array("Volume")

    @property
    def index(self) -> pd.DatetimeIndex:
        return self.__get_array("__index")

    # Make pickling in Backtest.optimize() work with our catch-all __getattr__
    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state


_set_legacy_module(_data_period, "openbacktesting._util")
_set_legacy_module(_strategy_indicators, "openbacktesting._util")
_set_legacy_module(_indicator_warmup_nbars, "openbacktesting._util")
_set_legacy_module(_Array, "openbacktesting._util")
_set_legacy_module(_Indicator, "openbacktesting._util")
_set_legacy_module(_Data, "openbacktesting._util")
