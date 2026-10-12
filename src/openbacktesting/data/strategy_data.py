"""Per-run market-data snapshot and stable series; does not register indicators."""

import numpy as np
import pandas as pd

from openbacktesting.data.core import _Data
from openbacktesting.indicators.types import (
    IndicatorCursor,
    IndicatorError,
    IndicatorHandle,
    immutable,
)

PRICE_COLUMNS = {"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}
DERIVED = ("hl2", "hlc3", "hlcc4")
DATA_NAMES = frozenset((*PRICE_COLUMNS, *DERIVED, "data_index", "df", "pip"))


class StrategyData:
    def __init__(self, data: _Data, cursor: IndicatorCursor):
        self._data = data
        self._cursor = cursor
        self._baseline: pd.DataFrame | None = None
        self._values: dict[str, np.ndarray] = {}
        self._handles: dict[str, IndicatorHandle] = {}

    def validate(self):
        """Check only at the initialization boundary; do not scan all data on each bar."""
        if self._baseline is None or self._cursor.phase != "init":
            return
        frame = self._data._full_frame()
        columns = frame.columns[frame.columns.isin(PRICE_COLUMNS.values())]
        current = frame.loc[:, columns]
        if (
            not current.equals(self._baseline)
            or not current.index.identical(self._baseline.index)
            or not current.columns.identical(self._baseline.columns)
        ):
            raise IndicatorError(
                "data-source-mutated",
                "strategy.data",
                "OHLCV or index changed; finish market-data preprocessing before first reading a market-data series",
            )

    def _capture(self):
        frame = self._data._full_frame()
        if not frame.index.is_unique:
            raise IndicatorError("invalid-data-source", "strategy.data", "Market-data index must be unique")
        columns = frame.columns[frame.columns.isin(PRICE_COLUMNS.values())]
        if len(columns) != 5 or set(columns) != set(PRICE_COLUMNS.values()):
            raise IndicatorError("invalid-data-source", "strategy.data", "Unique OHLCV columns are required")
        baseline = frame.loc[:, columns].copy(deep=True)
        values = {}
        for name, column in PRICE_COLUMNS.items():
            series = baseline[column]
            if pd.api.types.is_bool_dtype(series.dtype) or not (
                pd.api.types.is_integer_dtype(series.dtype)
                or pd.api.types.is_float_dtype(series.dtype)
            ):
                raise IndicatorError(
                    "invalid-data-source", "strategy.data", f"{column} must be a real-valued market-data column"
                )
            values[name] = immutable(series.to_numpy(dtype=np.float64, na_value=np.nan))
        self._baseline = baseline
        self._values = values

    def _derive(self, name):
        high, low, close = (self._values[key] for key in ("high", "low", "close"))
        valid = np.isfinite(high) & np.isfinite(low)
        with np.errstate(over="ignore", invalid="ignore"):
            if name == "hl2":
                values = (high + low) / 2
            else:
                valid &= np.isfinite(close)
                if name == "hlc3":
                    values = ((high + low) + close) / 3
                else:
                    values = ((high + low) + (close + close)) / 4
        return np.where(valid & np.isfinite(values), values, np.nan)

    def get(self, name: str) -> IndicatorHandle:
        self.validate()
        if self._baseline is None:
            self._capture()
        if name not in self._handles:
            values = self._values[name] if name in PRICE_COLUMNS else self._derive(name)
            self._handles[name] = IndicatorHandle(
                values,
                name=PRICE_COLUMNS.get(name, name),
                index=self._baseline.index,
                cursor=self._cursor,
                metadata={"kind": "data-source", "field": name, "version": "1"},
            )
        return self._handles[name]

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._values = {name: immutable(value) for name, value in self._values.items()}


from openbacktesting.helpers import _set_legacy_module

_set_legacy_module(StrategyData, "openbacktesting.strategy_data")
