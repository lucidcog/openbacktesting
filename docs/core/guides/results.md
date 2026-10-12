# Consuming results

## Persistent parameter-experiment results

`runtime.optimize()` and `optimizer.open_result()` provide per-run complete Portfolio saving and read-only result sets; see [parameter experiments](optimizer.md). They save only Portfolio and necessary management metadata, without logs or plots; ordinary-run default collection described below is unaffected.

## Portfolio complete report

`run()`, `run_inputs()`, and host `runtime.run()` still return the existing pandas Series, with an immutable `PortfolioSnapshot` in `attrs["portfolio_snapshot"]`. Complete facts are frozen at termination. `openbacktesting.portfolio.export_result(result)` or `get_snapshot(result).to_dict()` computes reports solely from frozen data without rerunning the strategy. Subsequent changes to original market data, trade tables, tags, or export copies do not alter snapshots; retaining `_strategy` is unnecessary. Snapshot string content stores internal facts; use exported dictionaries for cross-language transfer.

Report `schemaVersion="1.0.0"` is independent of trading-table version 4 and execution-policy version 2. `report_catalog()` returns fields, units, methods, availability, and the example-validation catalog. See the complete [Portfolio report example](../../../examples/advanced/portfolio_report.py). Hosts can directly consume:

| Field | Content |
| ----- | ------- |
| `run/context/semantics` | Actual execution/input ranges, termination reason, chart timezone, configuration, versions, and effective rate |
| `facts` | All orders, sizing, status events, fills, and entry/exit allocations, including unfilled requests |
| `trades.closedFragments/openLots` | Closed fragments and open lots; entry/exit legs, signals, prices, quantities, fees, returns, holding periods, MFE/MAE |
| `summary.all/long/short` | Account/directional contributions, trade statistics, close path, and monthly risk |
| `series` | Ordered account observations, closes, directional virtual equity, two benchmarks, closed cumulative results, and margin |
| `analysis` | Signal/direction decomposition; daily/weekly/monthly/quarterly/annual buckets; distributions/outliers; winning/losing streaks; temporal patterns; growth/drawdown intervals |
| `extensions.legacy` | Original statistics keys and conventions without replacing historical calculation definitions |

`allocation_id` is the closed-fragment primary key; partial exits may share `trade_id`, so do not deduplicate trade rows by lot ID. Quantities are actual executed quantities. A nonempty string tag is a signal; object tags contribute only a nonempty string signal and string comment, retaining all other original values. Internal exits without user signals return null.

New metrics use `value/unit/status/reason/methodId/sampleCount/reference`. Ratios are fractions; nanoseconds and integers exceeding JavaScript's safe range use decimal strings. Aware times encode absolute UTC nanoseconds with separate chart timezone; naive and ordinal times are marked separately. Counts/amounts with no fills are 0; means without samples are null; PF with no losses is null+unbounded; unsupported fields must not be filled with 0.

New `profitFactorMoney` divides total positive net amounts by total negative net amounts; legacy `Profit Factor` still aggregates trade returns. Monthly risk uses calendar-month account returns, effective monthly rate `(1+rf)^(1/12)-1`, population standard deviation/mean squared negative excess, and sqrt(12) annualization. Fewer than two months or invalid negative-equity denominators carry an insufficiency explanation. Directional curves use the same initial capital plus that direction's actual contribution; reversals and partial exits do not recognize future exit profits at entry.

Benchmarks are `input_start_close` and `first_entry_price`, rounded down to the asset quantity step, checked against minimum quantity/notional, retaining residual cash without fees. The second is inapplicable without entry. Calendar buckets use chart timezone, carry missing-data buckets forward with carriedForward, mark incomplete first/last buckets partial, and fabricate none after actual termination.

MFE/MAE measures gross price excursions during holding periods, frozen per fragment quantity on partial exits. same_close entries exclude pre-entry highs/lows; Open exits exclude post-exit highs/lows. Conditional orders without recoverable same-bar ordering carry partial lower bounds. Ordered intrabar paths use `sampled_bounds_v1`, grouping complete held bars' high/low points with preceding/following endpoints to calculate lower bounds without inventing within-group order. Growth ratios crossing a nonpositive equity base return undefined rather than 0. Commission load, Tukey outliers, growth segmentation, and fixed-path capital requirements are explicit local methods without TradingView numerical certification.

Margin calls, TV account capital requirements/margin-call liquidation quantities, cross-currency conversion, and contract multipliers are unsupported; bankruptcy/end_liquidation quantities are recorded separately. Portfolio describes a single-asset, single-currency, single-run result rather than a multi-asset portfolio account.

Full-account `compute_stats` recalculation retains facts and updates the effective rate and legacy statistics. Trade subsets lack the full-account path, clear the original Portfolio, and record `portfolio_diagnostic`; they cannot export a fabricated whole-account report. Built-in string optimization targets use lightweight candidate paths; custom callables can read complete Portfolios, and the final formal parameter rerun retains full facts. Execution/export does not automatically write files, request networks, or integrate webpages.

Statistics implementations and new pickles use actual definition paths under `openbacktesting.portfolio`. Legacy `results`, `stats`, and `_stats` modules were removed without historical-statistics pickle migration. `lib.compute_stats` remains the public recalculation convenience entry point.

## Native result fields

These are fields in the pandas Series returned by `run()`. Underscore-prefixed fields are native diagnostic data, not yet a stable cross-language Result Contract.

- `Start`
- `End`
- `Duration`
- `Exposure Time [%]`
- `Equity Final [$]`
- `Equity Peak [$]`
- `Return [%]`
- `Buy & Hold Return [%]`
- `Return (Ann.) [%]`
- `Volatility (Ann.) [%]`
- `CAGR [%]`
- `Sharpe Ratio`
- `Sortino Ratio`
- `Calmar Ratio`
- `Alpha [%]`
- `Beta`
- `Max. Drawdown [%]`
- `Avg. Drawdown [%]`
- `Max. Drawdown Duration`
- `Avg. Drawdown Duration`
- `# Trades`
- `Win Rate [%]`
- `Best Trade [%]`
- `Worst Trade [%]`
- `Avg. Trade [%]`
- `Max. Trade Duration`
- `Avg. Trade Duration`
- `Profit Factor`
- `Expectancy [%]`
- `SQN`
- `Kelly Criterion`
- `_strategy`
- `_equity_curve`
- `_trades`

## Trading fact tables (0.2)

Result `attrs.trading_schema_version=4` and `execution_policy_version="2"` identify trading semantics, with core version, instrument, execution/end policies, margin, costs, and existing input snapshots. Nonreconstructable callable fee configuration records `commission_not_reconstructable`; a function name is not treated as a replayable implementation.

| Field | Facts and granularity |
| ----- | --------------------- |
| `_orders` | All requests and latest states, including rejection, cancellation, expiry, and original stop |
| `_order_sizing` | Request-sizing snapshots for ordinary orders and OCO, linked by order_id rather than executed notional |
| `_order_events` | Frozen values for every state/trigger change, with run-wide sequence |
| `_fills` | One row per actual execution, retaining side, quantity, price, fee, phase, and reason |
| `_trade_allocations` | Entry/exit allocations from Fill to lots, linked by fill_id/trade_id/entry_fill_id |
| `_positions` | Gross exposure, net position, and gross/net profit/loss at normal bars and separate terminal observations |
| `_account_curve` | Corresponding balance, equity, fees, and margin |
| `_final_account` | Pure-value final-account dictionary |
| `_open_trades` | Remaining lots, entry identities, remaining entry fees, and unrealized profit/loss |
| `_trades` | Closed fragments, retaining common Size, Entry/ExitPrice, PnL, Commission, ReturnPct, SL/TP columns and adding allocation_id, exit_fill_id, exit_sequence identities |

Order.request returns a frozen NormalizedOrderRequest with normalized quantity, conditions, and read-only reduce_only/trade_id/tag_json fields; tag returns an independent copy. Author OrderRequest input is separate from this observation model. Result columns still derive from the normalized model, so author constructor-signature changes do not alter _orders columns or values. Same-version requests/results support pickle round-trips without guarantees of cross-version live-object resume.

`_order_sizing` has fixed column order: order_id, mode, source, value, equity, reference_price, budget, qty. The first three use pandas string; the rest use float64. qty-mode budget is NaN. Each registered order with a sizing snapshot has one row retained after cancellation/rejection/expiry. Submission-validation failure leaves no record; internal targets/protective orders have no sizing rows. Percentage value 20 means 20%; qty is the rounded requested amount, while `_fills` governs actual execution. Original `_orders/_order_events/_fills` columns/dtypes are unchanged; the sizing table retains its format. Version 4 adds closed-fragment exit links without changing execution-policy or author-settings snapshot versions.

Empty results retain columns. Reading these tables does not require `_strategy`, which serves Python debugging rather than a persistent trading protocol. JSON tags accept only finite numbers, strings, booleans, null, lists, and string-keyed mappings and are isolated from original objects after submission.

`Exposure Time [%]` is the fraction of all input bars whose normal Close snapshots have nonzero gross quantity, including open positions and net-zero hedges. Terminal liquidation does not rewrite the final exposure observation. `Commissions [$]` sums all Fill fees, including unexited lots. `# Trades` and win rate count closed fragments; `# Closed Lots` counts fully closed unique lots.

Full `lib.compute_stats` recalculation can use the saved position path. Trade subsets lack that path and return NaN exposure; whole-account exposure cannot be inferred from closed trades.

## Statistical benchmarks and recalculation

Each run's `attrs["statistics_initial_equity"]` records positive finite initial capital before first-bar matching. Total return, CAGR, equity peaks, and drawdowns use this principal. Equity tables remain the same length as input without fabricated timestamps. For initial capital 1000, first-bar fees 10, and unchanged prices thereafter, return and maximum drawdown are both -1%, and equity peak is 1000.

Buy-and-hold uses the first and last input Close independently of indicator readiness. For daily/weekly/monthly/annual resampling, the first bucket's return is its ending equity divided by initial capital minus one, retaining zero returns; subsequent buckets use adjacent ending equities. Annualized/risk metrics use the complete bucket sequence; Beta still uses adjacent market/account returns. Unrecovered first-bar drawdown contributes to magnitude and duration, with duration beginning at the first actual timestamp and zero for single-bar input.

Runs with `DataContext` group data and evaluate weekdays in chart timezone, retaining the current annualization-period inference without separate UTC conversion. Even with identical absolute fill times, per-bar equity, and total returns, changing chart timezone may change daily-return grouping, annualized returns, volatility, and Sharpe. This is the intended chart-date-aligned convention. Serial and parallel results agree within a fixed timezone; statistics need not match across timezones. Chart calendar days do not automatically represent exchange trading days; see the [chart-context tutorial](../../../examples/advanced/chart_context.py).

Equity indexes and fill times retain the run's chart timezone, recorded as `context.timezone` in its snapshot. Plot-axis UTC nanosecond strings identify absolute instants, while separate `timezone` defines display interpretation; both identify the same bar without modifying timestamp values to match wall-clock hours.

Full-account recalculation inherits initial capital; approximate trade-subset equity also starts there, with zero return for empty subsets. Historical results lacking this attribute fall back to first equity and cannot reconstruct unrecorded first-bar costs. Present attributes that are not positive finite numbers are explicitly rejected. Recalculation changes neither original trading facts nor run snapshots.

Runtime risk_free_rate defaults to zero, uses annual fractions (-1,1), and affects legacy risk formulas and new Portfolio monthly Sharpe/Sortino without accruing cash interest. `attrs["statistics_risk_free_rate"]` identifies the effective benchmark for these statistics; runtime `backtest_snapshot.settings` preserves original run settings.

`lib.compute_stats` inherits the most recent statistical rate when omitted. Historical results without the key use zero; present invalid keys are rejected. Explicit `risk_free_rate=0.0` overrides, while None is invalid. Repeated recalculation inherits the latest benchmark without rewriting the original run snapshot, modifying source results, or charging fees again; trade subsets retain original path-estimation boundaries. The [runnable tutorial](../../../examples/advanced/strategy_settings.py) demonstrates inheritance and explicit overrides.

Author `backtest_snapshot` is version 2; settings retains 16 flat fields, enum strings, and percentage values. Independent `attrs["commission"]` still describes the actual execution model and must not be passed back as author settings. Pure-value Commission metadata uses a complete kind/version object without nonreconstructable diagnostics; historical numeric/tuple export forms remain unchanged. New settings change neither trading-table columns nor matching-policy version and do not imply equivalent Pine ratios or matching semantics.

## Plotting data

With default collection enabled, successful results retain an independent frozen snapshot in `attrs["plotting_result"]`. Export a strict-JSON-compatible dictionary with `openbacktesting.plotting.export_result(result)`; see the [plotting guide](plotting.md). It reuses `_fills/_account_curve` facts; user markers are independent of fills and do not depend on `_strategy`.

## Strategy logs

Argument-free `bt.get_logs()` returns an independent `list[dict]` of all this run's records, or `[]` before execution; repeated reads do not consume records. Successful `attrs["strategy_logs"]` is an independent copy with identical content, without changing statistical keys or depending on `_strategy`. Logs already written remain readable after exceptions, including on_finish output; parameter/construction failures usually leave none. New run/run_inputs/optimize calls clear prior records without changing returned copies.

| Field | Meaning |
| ----- | ------- |
| `sequence` | Successful append sequence beginning at 1 per run; sole ordering basis |
| `level`, `message` | info/warning/error and original string; timestamps and locations are not inserted into message text |
| `phase` | init/on_start/next/on_order/on_fill/terminal_order/terminal_fill/on_finish |
| `bar_index` | Zero-based current input position; None without a current bar |
| `bar_time` | ISO 8601 input date label preserving precision and offset; None for nondatetime indexes or no current bar |
| `time_kind` | aware-datetime/naive-datetime/ordinal/none, distinguishing aware, naive, ordinary indexes, and no current bar |
| `recorded_at` | UTC system time with +00:00 at microsecond precision; may vary on rerun and does not order market data |
| `source_file`, `source_line` | Actual call file/virtual identifier and one-based source line; both None if unavailable |

bar_time faithfully records the run index label, already converted to chart timezone with context and retaining its local offset. It is not guaranteed to be opening time and does not subtract timeframe. recorded_at always records system UTC time rather than aligning historical bars. Early-bankruptcy terminal logs reference the actual processed position, not an unexecuted final bar. Source locations identify actually executed code; dynamic code may use `<string>`, and later file changes do not rewrite old records. Future hosts own console presentation and editor-snapshot mapping.

All records are retained by default without truncation above 10,000. Memory grows with count, message size, and export copies; disk storage, pagination, and recovery after forced process termination are not provided. Optimization retains only final formal-rerun logs, excluding candidates, other strategies, and global Python output. See the [consumption example](../../../examples/advanced/strategy_logs.py) for a complete execution recipe.

## Running closed-fragment totals

`Strategy.closed_trade_stats` is a frozen pure-value `ClosedTradeStats`, readable in callbacks and after completion and transferable through pickle. It accumulates completed closed-fragment net profit/loss including allocated fees; partial exits count individually, and empty means/win rates are None. Each run starts at zero and retains closures preceding exceptions. It does not replace result tables or include unrealized open-position profit/loss; `winning_profit` is not gross pre-fee profit. The [closed-statistics example](../../../examples/strategies/closed_trade_statistics.py) independently checks aggregation against `_trades.PnL`; see the [trading guide](trading.md#explicit-price-rounding-and-closed-fragments) for exact fields and timing.
