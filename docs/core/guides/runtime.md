# Host execution and optimization

To retain each combination's complete result, use `runtime.optimize()` from [parameter experiments and local Portfolios](optimizer.md). It is separate from `Backtest.optimize()`, described below, which returns the best score.

## Framework code: discovery and execution

Authors declare strategy settings through `@backtest(...)`; the framework supplies current chart data, context, and instrument specifications. Everything below is framework code. `namespace` is the global mapping from the user module successfully loaded by the host for this run. The core neither loads source nor provides a desktop runner.

```python
from openbacktesting import DataContext, Timeframe, runtime

strategy = runtime.discover(namespace)
schema = runtime.describe(namespace)
request = {
    "schemaVersion": schema["schemaVersion"],
    "schemaHash": schema["schemaHash"],
    "values": {"Moving-average period": 30},
}
result = runtime.run(
    namespace,
    request,  # For ConfigurableSma in the input guide; omit to use defaults.
    data=chart_data,
    context=DataContext(Timeframe.minutes(15), "Asia/Shanghai"),
    instrument=chart_instrument,
    settings={"cash": 20_000},
    options={"plotting": True},
)
snapshot = result.attrs["input_snapshot"]
```

The host supplies `chart_data`, the actual timeframe/timezone, and `chart_instrument` from this chart; copying example constants does not establish that the user is viewing a 15-minute chart. The complete offline [chart-context example](../../../examples/advanced/chart_context.py) demonstrates two instrument/timeframe configurations, chart-local hour conditions, statistical day boundaries, and repeated daylight-saving hours.

| Responsibility | User code | Framework code |
| -------------- | --------- | -------------- |
| Strategy logic and inputs | `Strategy`, `inputs`, `init/next` | Discover inputs and retain title-based requests |
| Default backtest settings | `@backtest(...)` | Apply sparse `settings` overrides to this run's effective values |
| Data, timeframe, timezone, instrument | No declarations | Inject `data/context/instrument` |
| Cache and plotting budgets | No declarations | `options` |
| Execution and results | Does not call execution APIs | Construct a fresh `Backtest`, execute, and save snapshots |

Discovery requires a mapping namespace with a nonempty `__name__` and exactly one nonabstract `Strategy` class defined in the module and decorated directly. Multiple aliases of a class are deduplicated; imported classes and derived classes without direct decoration are not entry points. Zero or multiple entries raise errors. The decorator returns the original class without a global registry. `discover/describe` requires no data and executes neither construction, init, nor next; scripts exporting only legacy bt are no longer runtime entry points.

`schema["backtest"]` uses `schemaVersion=2`; settings lists all [16 flat fields](author.md#flat-backtest-settings). The five enum categories export exact lowercase strings; commission and equity quantity retain author percentage units, without nested models.

Host `settings` accepts sparse mappings. Categorical fields accept the corresponding enum or exact table string, rejecting uppercase, whitespace, incorrect enums, legacy fields, and objects. Unoverridden fields retain declaration values; `default_qty_value=None` clears default quantity, and `max_gross_exposure=None` clears the exposure limit. All three type/value pairs follow the same rules: changing value alone retains type; repeating the same type does not require value; changing to another type requires value too, including 0 or valid None. The entire settings mapping is decoded and validated before strategy construction; failure neither applies partial changes nor modifies the declaration.

When saving/reading a configuration envelope, hosts must first validate version 2 and reject version 1 and unknown versions before using settings. Do not reinterpret legacy values automatically as new percentages. Runnable `read_settings` and rejection assertions are in the [host tutorial](../../../examples/advanced/strategy_settings.py). The immutable internal BacktestSettings snapshot/from_snapshot supports a complete 16-field JSON round-trip, rejecting missing/unknown fields, nested objects, and Python enums on restoration; sparse overrides go through runtime.

Runtime options accept only `indicator_cache_bytes/plotting/plotting_limits` and do not mix with author defaults. `settings/options` apply only to this session without changing class declarations. Native `Backtest(data, StrategyClass, ...)` retains explicit configuration and does not automatically merge the decorator; advanced hosts continue to construct and call native optimizers and backtest variants themselves.

## Timeframe and context

`TimeframeUnit` is a string enum: `SECOND/MINUTE/DAY/WEEK/MONTH`. `Timeframe(unit, multiplier)` is immutable and hashable; multiplier must be a strictly positive integer, rejecting bool, floats, and strings. Six convenience constructors are available: `seconds/minutes/hours/days/weeks/months`. Hours normalize to minutes; days, weeks, and months retain calendar units, so `days(7) != weeks(1)`. No fixed Enum lists every multiplier, and Pine timeframe-string parsing or conversion to seconds is not provided.

`DataContext(timeframe, timezone)` is immutable and uses a valid IANA timezone identifier; `UTC` or regional names such as `America/New_York` are recommended. runtime requires this and explicit `InstrumentSpec`, with market data indexed by a timezone-aware `DatetimeIndex`. Hosts provide UTC data consistently; the core also accepts other aware inputs and converts the index on a copy before strategy construction and init, preserving absolute instants, OHLCV, and market-closure gaps. It neither guesses timeframe, localizes unknown timezones, nor resamples automatically; naive input is rejected on the context-enabled path.

This run's `timezone` governs charts, strategy calendar tests, and statistical grouping. All three strategy index entry points directly expose the chart timezone, without manual conversion. After changing chart timezone, hosts should rerun with new context; previous results retain their old snapshot. Both trading and statistics may change for time-dependent strategies. Time-independent strategies can have identical equity but different annualized metrics; see [statistical conventions](results.md#statistical-benchmarks-and-recalculation). Timeframe does not change the current annualization-inference algorithm, and chart calendar days are not exchange trading days.

Shared memory transfers timestamps by absolute instant at original precision before restoring chart timezone; repeated daylight-saving hours retain distinct offsets. Plot axes continue to emit UTC nanosecond labels and timezone metadata without adding artificial offsets to UNIX timestamps. Desktop consumption and timezone-switch integration are not yet connected.

After construction, strategies read the actual timeframe through read-only `self.timeframe` in `init` and `next`; class fields, params, inputs, assignment, and deletion cannot override it. Low-level `Backtest` may omit `context`; then `self.timeframe is None`, preserving legacy data-entry behavior.

## Input and result snapshots

The existing input digest describes only inputs; changes to backtest settings do not change `schemaHash`. Requests are validated before strategy construction. Only request=None selects defaults; an empty dictionary is not ignored. Descriptions remain empty for strategies without inputs, and title-based requests to them are rejected. Exceptions propagate unchanged.

Statistics, trades, indicators, and plotting results retain their existing outlets. `result.attrs["backtest_snapshot"]` independently records strategy module/qualname, all resolved settings, chart context, instrument, runtime options, and core version with `schemaVersion=2` as pure JSON values. It contains neither source digests nor complete market data. Strategies with inputs retain separate `input_snapshot`. Changing description or request copies does not modify class declarations or existing results.

The host stops after each failed load rather than falling back to a previous namespace; runtime does not cache strategy instances. The host owns source identity, input-configuration ownership, and code-execution boundaries. Module loading executes user top-level Python; neither discovery APIs nor Workers are system sandboxes.

## Framework code: optimization and result consumption

Hosts also call optimization and consume results. The fragment below references the native optimization tutorial's main; the full file defines Sma4Cross, period constraints, and an explicit execution entry point. See the [unified examples](../examples.md).

[Complete source](../../../examples/advanced/parameter_optimization.py)

Search defaults to grid; `method="sambo"` requires the optimize extra. Put cross-process entry points inside `if __name__ == "__main__"`, following Python startup requirements. Where the platform defaults to spawn, the core emits a notice and uses a thread pool; advanced callers may explicitly override `openbacktesting.Pool`. Performance and startup behavior should not be assumed identical across platforms.

The core returns statistics, `_trades` details, and `_equity_curve` data; `return_heatmap=True` returns a parameter-score table without generating charts. Select examples from [examples/README.md](../../../examples/README.md): `strategies/` contains recommended author templates, while `advanced/` includes custom author examples and explicitly executed native tutorials, with categories identified by the index. New core functionality must add or update runnable examples, the index, and validation together. Examples ship with source and sdist, not the wheel; ML tutorials require the test extra and are marked as nonrecommended research.

New fields export with default descriptions and effective runtime snapshots but do not participate in input schemaHash. `risk_free_rate` defaults to zero with range (-1,1), and 0.02 means 2% annually; it does not enter the trading account. Enums and internal effective configuration are pickleable. Internal adaptation only divides commission/equity percentages by 100 before entering native Backtest, reusing Commission, DefaultOrderSize, and Slippage. Native Backtest/optimization retains its units and advanced-model entry points and does not read decorators automatically. See [statistical benchmarks](results.md#statistical-benchmarks-and-recalculation) and the [runtime example](../../../examples/advanced/strategy_settings.py).

## Host retrieval of logs after failure

Import `RunLogs` from the package root and pass a session separately through `runtime.run(..., logs=session)`. Then `session.get_logs()` reads records written before success or failure. Execution still returns Series and preserves the original exception object; the session does not belong in settings/options. Without a session, successful results still have `attrs["strategy_logs"]`, while failures have no additional public log outlet.

Sequential session reuse clears old records before strategy discovery and request validation. Concurrent reuse or reentry raises RuntimeError without clearing an active run; an incorrect type raises TypeError. Sessions may be reused after exit, and previously returned copies remain unchanged. The tested tutorial below demonstrates low-level and host exception retrieval and location fields:

[Complete source](../../../examples/advanced/strategy_logs.py)

grid and SAMBO candidates collect no logs; only the final formal rerun collects them, including the no-trade fallback. Search failure returns empty logs; final-rerun failure retains that run's records. Candidates still validate message types and normally evaluate expressions such as f-strings; candidate logs must not be used for scoring. MultiBacktest retains its statistics-summary interface without cross-dataset log merging. See [log results](results.md#strategy-logs) for fields and capacity boundaries.

## Consuming Portfolio

On success, call `openbacktesting.portfolio.export_result(result)` for a complete strict-JSON dictionary; the plotting function of the same name is in a separate module. Reports require no live strategy object and retain the original run configuration and effective statistical rate; persist or transmit only when the host explicitly needs it. Portfolio's independent contract does not change Worker RunResult or strategy.execute capabilities; web and desktop backtest integration is currently absent. See [result conventions](results.md#portfolio-complete-report).
