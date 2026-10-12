# Market data and stable handles

See the [data-source example](../../../examples/strategies/data_sources.py) for complete code; place the method fragments below in a Strategy subclass.

## Direct market-data access

`self.open/high/low/close/volume` and `self.hl2/hlc3/hlcc4` return read-only `IndicatorHandle` objects. Saved references and slices continue to follow this run's cursor and can be passed directly to `self.ta` in `init()`:

```python
def init(self):
    self.saved_close = self.close
    self.tail = self.close[-3:]
    self.average = self.ta.ema(self.close, length=20)
    self.weighted_average = self.ta.ema(self.hlcc4, length=20)

def next(self):
    if self.average.valid[-1] and self.saved_close[-1] > self.average[-1]:
        pass
```

`hl2=(H+L)/2`, `hlc3=(H+L+C)/3`, and `hlcc4=(H+L+C+C)/4`; the last excludes Open. Use `[-1]` for the current value and `[-2]` for the previous bar; `[0]` is the first value, rather than a Pine historical offset. Comparisons and arithmetic produce ordinary arrays that do not automatically follow the cursor; extract scalars before conditional tests. `.s/.df/np.asarray()` conversions are also snapshots of the prefix visible at that moment; full data explicitly saved during init is not withdrawn later.

Each read of `self.data_index/df` returns an ordinary pandas object for currently visible data. A saved object's length does not change with the cursor; deep copies and content isolation are not guaranteed. df retains original and additional columns and does not add derived columns automatically. `self.pip` retains the full-sample decimal-place estimate and is not a reliable exchange tick size.

The first read of any of the eight series captures the full OHLCV data and index; new series in the same run use that snapshot. **Complete market-data preprocessing before the first read of a new series**: later init changes to OHLCV, dtype, or index raise `data-source-mutated` on a subsequent series read, indicator registration, or completion of init. Adding only extra columns is unaffected. Mixing new series with market-data writes during execution is unsupported: legacy `self.data/df` remains writable, but new handles do not follow writes and immediate detection is not guaranteed. Using only the legacy interface does not enable the new snapshot constraints.

New sources use float64 consistently, accepting integers, floats, and pandas nullable integer/float types; booleans, complex numbers, object types, and similar types are rejected, and the index must be unique. Missing volume remains NaN; non-finite inputs and derived overflow are marked invalid through valid without zero filling. Reading sources does not increase the indicator count; neither source nor indicator validity affects per-bar `next()` calls.

All 11 property names above are reserved. Rename colliding strategy fields, methods, InputSpec binding fields, and runtime parameters, for example from `close` to `close_threshold`. An InputSpec display `title="close"` remains valid. The legacy `self.data` entry point is retained.

## Current bar position and state

`self.bar_index` is the zero-based integer position of the current input bar; `self.data_index` is the pandas label index of visible history, and `self.data.index` is retained. Top-level `self.index` has been removed, and that name is no longer reserved.

`self.bar_state` returns a frozen `BarState`: `is_first` denotes position 0, and `is_last` denotes the final bar of the fixed input. Both are true for single-bar input; early termination does not turn the last visited bar into `is_last`. Saved states are snapshots and do not update with the cursor. Import the type from `openbacktesting` or `openbacktesting.strategy`.

State is readable in `on_start()` (the first bar), `next()`, and order/fill notifications, including terminal notifications. Reads during `init()`, `on_finish()`, or after execution raise `RuntimeError`. Each run independently maintains a constant-size current context.

`bar_index/bar_state/data_index` are reserved read-only properties: colliding class fields, methods, Input bindings, runtime parameters, instance assignment, and deletion are prohibited. Input display titles may still use these names.

See [bar_states.py](../../../examples/strategies/bar_states.py) for a complete example. `next()` runs from the first bar, with only one visible history item: check length before reading `[-2]`, and check the corresponding channel's `valid[-1]` before consuming indicators.
