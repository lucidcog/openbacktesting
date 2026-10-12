# Examples and execution evidence

## Parameter-experiment result database

This tutorial actually executes selective exhaustive input search, per-report saving, cancellation/recovery, and two sorting methods, retaining only Portfolios.

[Complete source](../../examples/advanced/optimizer_results.py)

The selection index directly references the original README; complete code comes from tested files.

[Example index](../../examples/README.md)

## strategies/ema_macd.py

[Complete source](../../examples/strategies/ema_macd.py)

## strategies/custom_indicators.py

[Complete source](../../examples/strategies/custom_indicators.py)

## strategies/data_sources.py

[Complete source](../../examples/strategies/data_sources.py)

## strategies/confirmed_events.py

[Complete source](../../examples/strategies/confirmed_events.py)

## strategies/ema_inputs.py

[Complete source](../../examples/strategies/ema_inputs.py)

## strategies/all_inputs.py

[Complete source](../../examples/strategies/all_inputs.py)

## advanced/native_run.py

[Complete source](../../examples/advanced/native_run.py)

## advanced/composable_strategies.py

[Complete source](../../examples/advanced/composable_strategies.py)

## advanced/multiple_time_frames.py

[Complete source](../../examples/advanced/multiple_time_frames.py)

## advanced/parameter_optimization.py

[Complete source](../../examples/advanced/parameter_optimization.py)

## advanced/machine_learning.py

[Complete source](../../examples/advanced/machine_learning.py)

## strategies/cross_signals.py

[Complete source](../../examples/strategies/cross_signals.py)

## First backtest and indicator trials

### Minimal author strategy

[Complete source](../../examples/strategies/first_backtest.py)

### Host runtime entry point

[Complete source](../../examples/advanced/run_author.py)

### Individual indicator trials

[Complete source](../../examples/advanced/indicator_reference.py)

## Trading lifecycle and fees

[Complete source](../../examples/strategies/trading_lifecycle.py)

## Native fractional quantities and target positions

Three sizing modes, explicit default-quantity overrides, frozen sizing snapshots, and existing budget helpers; amount/percentage pending orders are canceled after demonstration.

[Complete source](../../examples/strategies/fractional_sizing.py)

## Expiry and grouped orders

init constructs mixed percent/amount intents, converted consistently at submission while preserving OCO exclusivity and protective terminal states.

[Complete source](../../examples/strategies/managed_orders.py)

## Plot declarations and host export

[Complete source](../../examples/strategies/plotting.py)

[Complete source](../../examples/advanced/plotting_export.py)

## Chart context and declaration overrides

[Complete source](../../examples/advanced/chart_context.py)

## Strategy settings and statistical recalculation

The tutorial covers five enum categories, three commission modes, two quantity modes, two slippage modes, JSON overrides/version validation, rejected type changes, and clearing. It distinguishes author single-mode fees from low-level composite fees; see `test_examples.py` for execution validation.

[Complete source](../../examples/advanced/strategy_settings.py)

## First/last bar state and position

[Complete source](../../examples/strategies/bar_states.py)

## Strategy logs and retrieval after failure

[Complete source](../../examples/strategies/strategy_logs.py)

[Complete source](../../examples/advanced/strategy_logs.py)

## Local built-in capabilities

Three examples demonstrate explicit price rounding/colors, eight indicator entry points, and fee-inclusive closed-fragment statistics, with market data and specifications consistently injected by the host.

[Complete source](../../examples/strategies/local_value_helpers.py)

[Complete source](../../examples/strategies/local_builtin_indicators.py)

[Complete source](../../examples/strategies/closed_trade_statistics.py)

## All Portfolio report regions

Partial exits, remaining lots, signals, MFE/MAE, and frozen exports all arise from actual trades. The example traverses the field catalog and verifies every analysis region; the chart-context example also checks local-calendar buckets.

[Complete source](../../examples/advanced/portfolio_report.py)
