# Indicator contracts and capabilities

The core provides its own indicator catalog, batch computation, and strategy registration on fixed `pandas-ta-classic==0.8.32`. The current catalog has 247 classified entries: 211 ordinary indicators, 24 utilities/confirmed events, and 9 available patterns. Three further entries, cdl_pattern, vp, and tos_stdevall, are unavailable for trading calls. Counts come from actual artifacts; the advertised documentation count of 224 is not an acceptance constant.

Sources of truth are the [fixed catalog](../../../src/openbacktesting/indicators/catalog.json), [per-entry contract tests](../../../tests/test_indicator_catalog.py), and subpackage implementation records. Upstream upgrades require a fresh review of entries, parameter domains, outputs, and causality; reflection must not automatically expose newly added functions.

Fragments below illustrate local calls. `frame` is a caller-prepared market-data DataFrame; strategy methods belong in a Strategy subclass. [Examples](../examples.md) provide complete executable code.

## API and backend boundaries

```python
from openbacktesting import indicators

result = indicators.compute("ta.ema", frame, parameters={"length": 20})
print(result.s)
print(indicators.describe("ta.macd").outputs)
```

Strategies consistently call built-in indicators through `self.ta`. Series-method signatures, defaults, and return types are generated from the reviewed catalog and distributed in the wheel; immediate crossing tests have a separate implementation:

```python
def init(self):
    self.ema = self.ta.ema(length=20)
    self.macd = self.ta.macd()
    self.smoothed = self.ta.ema(self.macd.histogram, length=5)

def next(self):
    average = self.ema[-1]
    histogram = self.macd.histogram[-1]
```

Single outputs retain `IndicatorHandle`; multiple outputs provide read-only named results. Channel views are created at initialization, so repeated property reads neither copy history nor register again. MACD `line` and canonical `macd` alias the same object; `histogram` and `signal` are separately readable. BBands provides `lower/middle/upper/bandwidth/percent`. Multiple outputs support canonical keys and `ready/valid/metadata/df`; they neither implicitly choose a main line for arithmetic nor accept numeric channel indexes.

The first `source` argument of single-input methods accepts a market-data column name or same-run single channel, such as `self.ta.ema("Open", length=20)`; omission or `None` selects default market data. Crossings use `self.ta.crossover(left, right)`, and event values use `self.ta.valuewhen(condition, source, occurrence=0)`, accepting column names or same-run single-channel handles. Other multi-input methods use `inputs`; supplying both nonempty `source` and `inputs` raises an error. Missing nonstandard inputs such as benchmark are not inferred; arbitrary ndarray or cross-run handles are rejected. `backend` and `required_outputs` retain existing options, and required outputs always use canonical names (`macd` for the MACD main line).

### Crossing series and immediate tests

| Entry point | Return | Phase and purpose |
| ----------- | ------ | ----------------- |
| `self.ta.cross/crossover/crossunder(left, right)` | `IndicatorHandle`, valid 0/1 values, invalid NaN | Register in init; compose further or read `[-1]` in next |
| `self.ta.is_cross/is_crossover/is_crossunder(left, right)` | Python `bool` | Directly test the latest two visible input bars for next branches; registers no indicator and does not affect per-bar callbacks |

Both groups use identical rules: crossover requires current left strictly above right and previous left less than or equal to right; crossunder reverses this. Current equality is not a crossing. With fewer than two bars or invalid comparison values, `is_*` returns `False`, while series retains NaN and `valid` masks.

`is_*` accepts single-channel handles, list/tuple, NumPy arrays, pandas Series, or numeric thresholds. Series uses the latest two positions. Handles obey visible cursors and `valid` masks; NaN/infinity is invalid. Pass `self.close` rather than a column-name string and select channels from multiple outputs first. `inputs/backend/required_outputs` is unsupported. Callers must truncate independent arrays to the current moment; calling in init tests the last two values of the full input without producing a series.

See [cross_signals.py](../../../examples/strategies/cross_signals.py) for complete usage of both entry-point groups.

`ta` is reserved on strategies; colliding class fields, methods, Input fields, parameters, and instance assignments must be renamed, without affecting Input display titles. Registration methods are available only in `init()`. During development, run `uv run --locked python scripts/generate_indicator_api.py --check`; after catalog changes, run `uv run --locked python scripts/generate_indicator_api.py` rather than editing generated runtime files. See the method-interface implementation record for implementation and acceptance evidence.

Register built-in indicators through `self.ta` in `init()`. `inputs` mappings accept only market-data column names or same-run single-channel handles. `backend` and `required_outputs` are runtime options; all other parameters are strictly validated against definitions. Unknown parameters, bool in place of integers, non-finite numbers, and invalid parameter relationships are rejected. Unpublished upstream `**kwargs` are not forwarded.

The catalog fixes each backend: existing wrappers use `pandas-ta-classic.native` with explicit `talib=False`; new local formulas and revised NVI/PVI use `openbacktesting.numpy`, without TA-Lib/Numba extras. Tests block TA-Lib imports while simulating its installation; installed-library state does not alter built-in calls. Only SMA additionally offers `backend="pandas.sma"` as evidence of replacement-implementation contracts. Unknown backends fail explicitly without fallback.

Indicators live under the `indicators/` subpackage, organized by category, with one file per available indicator, such as `overlap/ema.py`, `overlap/sma.py`, and `momentum/macd.py`. Native/Pandas and other implementations of one indicator remain in its file. Each file owns explicit library calls and semantic mapping; no `backends/` directory exists.

`types` contains definitions, results, and cursors; `common` validates shared outputs; `calculus` handles finite-history mathematics; `registry` explicitly binds ID, backend, function, and implementation version; `runtime` supplies catalog, pure computation, and caching. Indicator modules import neither registry, runtime, strategy, nor Worker. They are invoked only on cache-miss batch computation without adding per-bar wrappers.

The catalog owns public defaults, parameter domains, outputs, and aliases; private wrappers receive required normalized parameters. Reviewed vendor column names map to canonical output channels. Reordered correct columns normalize successfully; missing, duplicate, or unknown columns raise `output-contract`, and index misalignment raises `index-mismatch`. Adapter `IndicatorError` passes through unchanged; actual third-party exceptions are wrapped as `calculation-failed`. Reindexing and zero filling must not hide violations.

Legacy `indicator_api`, `indicator_methods`, and `indicator_types` remain same-object compatibility exports supporting old imports and historical pickle reads; new implementations and types live in the subpackage. Calls to `indicators.compute/catalog/describe` and `self.ta` are unchanged.

## Time, readiness, and results

Direct market-data properties `self.open/high/low/close/volume/hl2/hlc3/hlcc4` reuse `IndicatorHandle` and the same-run cursor, supporting `self.ta.ema(self.close)`. Source metadata is marked `data-source`; sources are not registered indicators and do not affect per-bar callbacks, though their valid masks affect consuming indicators. Saved references and slices update dynamically; arithmetic and explicit conversions remain snapshots.

First access to a new series captures an independent OHLCV snapshot. Subsequent init reads, custom/built-in registration, and the init completion boundary detect changed market data and raise `data-source-mutated`; preprocess data earlier. Extra columns do not affect this check. New sources use float64 and finite masks, with fixed derived formulas calculated at most once per run. Per-bar execution does not scan the full table. Mixing legacy DataFrame writes during execution with new sources is unsupported without real-time detection guarantees. Pure legacy access retains original behavior. See the implementation design and [core usage](../../../README.md) for details.

`self.data_index/df/pip` delegates to the original data interface and must not be confused with isolated `.s/.df` handle conversions: saved ordinary pandas objects do not follow the cursor and need not be deep copies; pip remains an estimate. These 11 names and `bar_index/bar_state` are reserved. Rename Python fields when migrating colliding strategy parameters; display title is unaffected.

Each run has an independent cursor. Registered indicators, ordinary-container aliases, named channels, and time slices read prefixes through that cursor; backends are not called per bar. Required-output masks serve readiness diagnostics only; the execution loop does not scan indicator readiness. Initialization sees full history, so the framework cannot prevent authors from deliberately saving future information or writing noncausal callables in `init()`.

`ready` means minimum-history conditions are satisfied; `valid` means a channel has a consumable value on the current bar. `ready_at/first_ready` combines minimum history with required-output validity for diagnostics; `required_outputs=[]` checks only minimum history. None controls strategy execution; consumers handle invalid data themselves. NaN/Inf is not valid numeric data. Current-input validity is required by default; valuewhen retains confirmed historical event values, and pivot_points retains previous complete-period levels, judging validity by their own outputs. Other missing-data recovery is declared individually, without automatic zero filling or backward filling.

`next()` starts at position 0 and runs once per normally reached bar, including insufficient history, all-NaN inputs, and intervening gaps. Only one history item is visible on the first bar; check length before reading the previous bar and channel `valid` before consuming indicators. In particular, do not use `bool(NaN)` to test signals. Existing orders and stops continue through broker causal phases; bankruptcy or exceptions terminate callbacks. After normal completion, exhaustion of funds, or exceptions, diagnostic handles restore full history and prohibit further registration.

`.s`, `.df`, and `np.asarray()` explicitly snapshot the visible prefix; writes to copies do not contaminate computed results. Raw buffers are backed by nonwritable bytes and cannot regain write permission through `setflags`. Cache templates and different runs do not share cursors; pickle restoration preserves read-only constraints.

Result `attrs["indicator_snapshot"]` records ID, semantic version, normalized parameters, input-content identity and composition sources, backend, `implementation_version`, dependency/core versions, dtype, unit descriptions, and missing-data/readiness policies, alongside existing `input_snapshot`. Custom `ind()` is marked custom without shared caching or guarantees of arbitrary-callable reproducibility.

## Capabilities and special entries

| Category | Ordinary indicators | Utilities/confirmed events | Patterns |
| -------- | ------------------: | -------------------------: | -------: |
| candles | 2 | 0 | 9 |
| cycles | 8 | 0 | 0 |
| momentum | 62 | 0 | 0 |
| overlap | 49 | 0 | 0 |
| performance | 3 | 0 | 0 |
| statistics | 13 | 0 | 0 |
| trend | 29 | 2 | 0 |
| utility | 0 | 22 | 0 |
| volatility | 20 | 0 | 0 |
| volume | 22 | 0 | 0 |

DPO is fixed to noncentered, no-lookahead mode. Ichimoku disables Chikou and future extension, returning only same-index `span_a/span_b/tenkan/kijun`. CPR uses only the previous input bar, without cross-timeframe resampling or future virgin-level recognition. VWAP groups by input datetime index at daily/weekly/monthly frequencies without inferring exchange sessions.

Nine patterns are available through cdl_ methods: doji, inside, engulfing, hammer, shootingstar, harami, morningstar, eveningstar, and marubozu. Integer 0 means valid but untriggered; insufficient history and missing data use separate valid masks. Positive doji denotes a doji only, while inside's sign denotes current candle direction; neither is an independent long/short recommendation. engulfing/harami retain 80/100 strength scores. Eight calls use fixed classic native functions; doji locally compares bodies with preceding-window range thresholds to avoid implicit TA-Lib and full-sample epsilon. Unreviewed cdl_pattern dispatch remains unavailable.

## Custom indicators and reuse

Register custom calculations only in `init()` with `self.ind(func, *args, name=None, **kwargs)`. Legacy `self.I` has been removed without an alias; built-in formulas use `self.ta` consistently.

The same pure function may be registered with multiple parameter sets or placed in an ordinary importable module for reuse by other strategies. Every registration executes the function and returns an independent handle without custom caching. DataFrame column order determines channel order; specify channel names through a `name` list. Select a channel with `result['middle']` before composing through `self.ta` or plotting.

To compose existing indicators, use a function receiving `ta` and sources, and retain handles in containers such as `NamedTuple`; containers have no computation lifecycle. Do not store one run's handles in global objects for reuse by subsequent runs. The complete example declares strategies with `@backtest` and places no orders by default; example tests actually execute another strategy's reuse of the same function.

[Complete source](../../../examples/strategies/custom_indicators.py)

`init()` sees complete input history, so rolling formulas must depend only on current and past data; handles cannot correct future leakage already introduced by negative shifts or similar operations. In the example, `.s` is a full input snapshot for pure computation, while strategy attributes store registered handles. Arithmetic likewise yields ordinary arrays; register them again through `ind` when dynamic reading is needed.

Custom-result `valid` defaults to finiteness, and `ready` defaults to all true; boolean False and integer 0 are valid values rather than insufficient-history markers. `warmup` and its metadata were removed; `ind(..., warmup=...)` explicitly raises `TypeError` rather than forwarding it to the callable. Consumers check every channel's validity themselves. To consume a masked single channel, pass `source.s.where(source.valid)`; `ind` neither propagates argument-handle masks automatically nor validates their run ownership. `required_outputs`, explicit output masks, version identity, and caching are not registration options here.

## `ind()` consumption constraints

| Consumption | Current behavior and migration constraints |
| ----------- | ------------------------------------------ |
| `ind(callable, *args, **kwargs)` | Retains call syntax, naming, and positional-array rules; returns `IndicatorHandle` |
| `len/shape/ndim/dtype`, indexing, comparisons, basic arithmetic, `float/bool` | Reads the current prefix; scalar conversion reads the latest value |
| Attributes, aliases, nested list/dict/tuple, channel unpacking, slices | Retains cursor references without per-bar attribute rebinding |
| Series/DataFrame returns | Index must exactly match market data; replace legacy RangeIndex results with the input index or explicitly use `.to_numpy()` for positional arrays |
| `.s/.df/np.asarray` | Explicit snapshots, not automatically growing references |
| Arithmetic-derived results | Ordinary arrays; explicitly register again through `ind()` for controlled per-bar reads, without automatic expression graphs |
| In-place assignment, ufunc `out`, `np.asarray(copy=False)` | Explicitly rejected; use `.copy()` before modifying |
| ndarray type identity or arbitrary methods | Compatibility is not guaranteed; migrate to public consumption methods |
| `resample_apply`, SignalStrategy, native fractional trading | Uses unified handles and preserves price units; see the [trading guide](trading.md) for semantics |
| Historical `_Indicator` pickle | Old classes are retained for historical samples; new strategies consistently return handles |

See the [built-in indicator author script](../../../examples/strategies/ema_macd.py): authors declare strategies with `@backtest`, and the framework takes over through `runtime`. Desktop and Worker integration was not added in this work.

## Performance and resource scope

`Backtest(..., indicator_cache_bytes=64 * 1024 * 1024)` configures each cache instance's LRU retained-byte budget; `0` completely disables reuse. Accounting covers arrays, masks, and indexes, but excludes active strategy references, temporary arrays, Python objects, and market data, so it is not a process RSS limit. Oversized results compute normally without retention; eviction does not damage active handles, and failures are not cached.

With caching enabled and entries retained, identical registrations within a run are reused. grid optimization shares caches across threads and coalesces concurrent same-key computations; spawn workers have independent caches. Only call tokens are serialized, not locks. Sequential SAMBO runs share this search's cache. The optimization creates and closes its pool; parent finally releases this cache, and worker caches are released with pool exit. Global cross-process hits are not guaranteed, and the final best run may recompute.

grid allocates original market-data shared memory once and reuses descriptors across batches; the parent owns release. Strategies still receive private writable market-data copies so user changes cannot contaminate other candidates. Shared columns are rebuilt with explicit `copy=False` and checked for shared memory; indexes are copied independently, and run-private data still materializes. The entire backtest is not claimed to be zero-copy.

Each registration rereads and hashes required inputs from writable DataFrames, a necessary cost to prevent incorrect cache hits. Registered results are not retrospectively recomputed. There is no explicit frozen-market-data API, persistent cache, or cross-process result sharing. See implementation records for actual timings, cache benefits, and regressions; reduced operation counts do not imply speedups for every workload.

Performance acceptance covers up to 100,000 bars, focusing on single strategies with 10, 30, or 50 distinct indicators and repeated registration, measuring initialization, backend computation, per-bar consumption, and total time separately. Detailed data is in the implementation record.

## Adding or replacing indicators

1. Add an indicator file in the appropriate category, explicitly invoking a reviewed algorithm through stateless functions and mapping channels; future patterns likewise require individual files.
2. Declare parameters, outputs/aliases, fixed options, status, and validity contracts in `indicators/catalog.json`; wrappers must not duplicate defaults.
3. Explicitly register function and implementation version in `indicators/registry.py`; implementations of one indicator remain in its file. Versions enter metadata and cache identity, so mapping changes require version updates.
4. Run `uv run --locked python scripts/generate_indicator_api.py`; add independent upstream reference values, parameter boundaries, gaps, short histories, prefix-causality, and exception tests. Integrity tests verify the catalog, 244 currently available IDs, independent files, and bindings; review and update the set when adding indicators.
5. Update provenance manifests, category capability counts, and documentation. Run `uv run --locked python scripts/check_package.py`, relevant pytest tests, builds, and isolated wheel validation. Performance comparisons remain multi-indicator strategies with at most 100,000 bars.

For example, EMA in `overlap/ema.py` invokes a fixed algorithm and names its single channel; MACD in `momentum/macd.py` maps vendor columns to `macd/histogram/signal`; SMA in `overlap/sma.py` maintains native and Pandas implementations together. Strategy authors continue using the `self.ta` examples at the start of this page.

## New capabilities and migration

This round added 53 available entries: 20 ordinary/composite indicators, 22 series utilities, 2 confirmed Pivots, and 9 patterns. doji/inside were previously deferred entries, so the net increase in catalog IDs is 51. Channels, aliases, and TradingView article counts are not indicator counts.

- Ordinary indicators: smi_stochastic, crsi, pmo, rmi, alligator, gator, atr_stop, volatility_stop, ma_envelopes, starc, ac, ibs, frama, wavetrend, adr, rvol, rci, iii, wvad, pivot_points.
- Utilities: highest/lowest, highestbars/lowestbars, rolling_sum/rolling_count, cum, running_max/running_min, change/shift/range, percentrank, percentile_nearest_rank/percentile_linear_interpolation, cross/crossover/crossunder, barssince/valuewhen, rising/falling.
- pivothigh/pivotlow output value/pivot_bar/confirmed_at when the right window completes, without backfilling the original extreme; ties select the rightmost extreme. All time indexes are zero-based input bar positions.

```python
def init(self):
    self.fast = self.ta.ema(length=10)
    self.slow = self.ta.ema(length=30)
    self.cross = self.ta.crossover(self.fast, self.slow)
    self.event_price = self.ta.valuewhen(self.cross, "Close")
    self.pivot = self.ta.pivothigh(left=3, right=3)
    self.pattern = self.ta.cdl_engulfing()
    self.levels = self.ta.pivot_points(inputs={"anchor": "PeriodStart"})

def next(self):
    if self.pivot.value.valid[-1]:
        confirmed_price = self.pivot.value[-1]
    if self.pattern.valid[-1]:
        score = self.pattern[-1]
```

See the [expansion example](../../../examples/strategies/confirmed_events.py) for a complete runnable strategy. Callers must explicitly provide a 0/1 PeriodStart series; initial history without an anchor is not a complete period. Traditional, Fibonacci, Woodie, Classic, DeMark, and Camarilla formulas consume only the previous complete period, with Woodie also consuming the new period's Open. Current-period highs do not change confirmed levels. Exchange sessions are not inferred, and this is not equivalent to arbitrary TradingView daily-data settings.

See [frozen contracts](../../../tests/fixtures/indicator_expansion/contracts.json) for defaults, seeds, missing-data rules, thresholds, and sources, and the [disposition inventory](../../../tests/fixtures/engine-indicator-coverage-disposition.json) for complete research-candidate ownership. Utilities use fixed windows and explicit missing-data rules without promising Pine dynamic length, implicit na skipping, repainting, or per-tick behavior. Alligator applies no plotting shift; Volatility Stop starts on the bar after its first reversal without retroactively clearing prefixes. Ranking operations work by window without full-sample quadratic matrices.

Five existing entries raised semantic/implementation versions to 2: NVI/PVI update an index by multiplying price ratios (length is the price interval, while volume compares adjacent bars), rather than accumulating percentage returns. Missing values/zero previous prices yield invalid output while preserving internal state. Squeeze/Squeeze Pro use_tr actually switches between true range and high-low; MSW rejects period=1. Rerunning old strategies may change results; old pickles read stored values without automatic recomputation. Existing smi remains Ergodic; the new stochastic momentum entry is smi_stochastic.

## Local anchors, finite observations, and explicit parameters

`ta.anchored_vwap` and `ta.anchored_vwap_bands` take `source`, `volume`, and `anchor` inputs. Strategies bind same-chart column names or handles, not pandas Series. Anchors must be complete and strictly 0/1; resetting precedes accumulation of the current row, and values before the first anchor are invalid. Non-finite source or volume makes that row invalid and skipped, but resets still execute on missing rows. Finite negative volume raises an error; zero volume retains a result when positive cumulative volume exists, otherwise it is invalid. Band width is volume-weighted population standard deviation times `stdev_mult`; the first positive-volume observation has zero width. Channels are fixed as `vwap/lower/upper`; overflow raises a calculation error.

`ta.mode` windows over the most recent `length` finite observations rather than consecutive bars. Tied frequencies select the smallest numeric value, including when all values are unique. Missing values do not consume the window, and missing rows remain valid after it fills. Internal windows, frequency counts, and candidate heaps are bounded, while output history still grows with input length.

Five extended parameters retain original default numerical outputs and valid masks: `true_range(handle_na=True)` uses H-L when the previous close is missing; the current Close may be missing, but H/L must be finite and ordered, and a zero first-bar range remains zero. `kc(use_true_range=False)` uses smoothed H-L ranges. `alma(floor=True)` rounds the weight center down while retaining fixed-backend weight direction. `linreg(offset=...)` reads position `length-1-offset` on the current window's fitted line without shifting the series; negative offsets extrapolate only the current fit, and `length=1` remains invalid. `pivot_points(developing=True)` uses the current anchored interval and is valid on the first anchor bar; invalid OHLC keeps that interval invalid until reset, and Woodie does not support this mode.

These APIs are local contracts, not proof of pointwise TradingView equivalence; conditional anchors do not infer exchange sessions. See the [local indicator example](../../../examples/strategies/local_builtin_indicators.py) for all eight calls and per-channel guards.
