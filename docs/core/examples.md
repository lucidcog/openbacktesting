# Runnable examples

Start with the [first backtest](quickstart.md) for a complete copyable script. The examples below are included in a source checkout or source distribution. An installed wheel includes sample data but not this examples directory.

## Run a complete script

From the repository root, run a direct tutorial:

```sh
uv run --locked python examples/advanced/native_run.py
```

To run a decorated strategy, use the example runner to supply its data and settings:

```sh
uv run --locked python examples/advanced/run_author.py examples/strategies/ema_macd.py
```

[Example index](../../examples/README.md) includes prerequisites and commands.

## Choose by task

| Example | What it demonstrates | How it runs |
| --- | --- | --- |
| [advanced/optimizer_results.py](../../examples/advanced/optimizer_results.py) | Select inputs; save complete Portfolios and reopen for sorting | Run directly |
| [strategies/local_value_helpers.py](../../examples/strategies/local_value_helpers.py) | Tick rounding and per-bar gradients | Use `run_author.py` |
| [strategies/local_builtin_indicators.py](../../examples/strategies/local_builtin_indicators.py) | Conditional VWAP, mode, and five parameter extensions | Use `run_author.py` |
| [strategies/closed_trade_statistics.py](../../examples/strategies/closed_trade_statistics.py) | Partial exits with fees and frozen statistics | Use `run_author.py` |
| [strategies/strategy_logs.py](../../examples/strategies/strategy_logs.py) | Three log levels, nonfatal error logs, explicit exceptions, and end records | Use `run_author.py` |
| [advanced/strategy_logs.py](../../examples/advanced/strategy_logs.py) | Timestamps, bars, source lines, failure retrieval, reruns, and host sessions | Run directly |
| [strategies/bar_states.py](../../examples/strategies/bar_states.py) | First-bar callbacks, boundary states, positions, labels, and local validity guards | Use `run_author.py` |
| [strategies/custom_indicators.py](../../examples/strategies/custom_indicators.py) | Custom functions, two parameter sets, named outputs, and reusable composition | Use `run_author.py` |
| [strategies/plotting.py](../../examples/strategies/plotting.py) | Color Input, Color/strings, transparency, panes, and per-bar coloring | Use `run_author.py` |
| [advanced/portfolio_report.py](../../examples/advanced/portfolio_report.py) | All report sections, partial-exit identities, MFE/MAE, signals, and frozen JSON | Run directly |
| [advanced/plotting_export.py](../../examples/advanced/plotting_export.py) | Color overrides, configuration replay, frozen snapshots, strict JSON, signals, and fills | Run directly |
| [strategies/trading_lifecycle.py](../../examples/strategies/trading_lifecycle.py) | Order events, rejection, partial fees, accounts, and end-of-run policies | Use `run_author.py` |
| [strategies/fractional_sizing.py](../../examples/strategies/fractional_sizing.py) | Three sizing modes, default overrides, frozen snapshots, named targets, and reduce-only | Use `run_author.py` |
| [strategies/managed_orders.py](../../examples/strategies/managed_orders.py) | Expiry, mixed-size OrderRequest OCO, protection, and trailing stops | Use `run_author.py` |
| [strategies/first_backtest.py](../../examples/strategies/first_backtest.py) | First backtest: EMA registration, stepwise decisions, and decorator declarations | Use `run_author.py` |
| [advanced/strategy_settings.py](../../examples/advanced/strategy_settings.py) | Five enum categories, flat overrides, JSON versions, and interest recalculation | Run directly |
| [advanced/chart_context.py](../../examples/advanced/chart_context.py) | Instrument/timeframe injection, chart-local hours, statistical day boundaries, and DST repeated hours | Run directly |
| [advanced/run_author.py](../../examples/advanced/run_author.py) | Host loads author scripts and reads results | Run directly |
| [advanced/indicator_reference.py](../../examples/advanced/indicator_reference.py) | Explore by indicator ID and check each channel for validity | Run directly |
| [strategies/ema_macd.py](../../examples/strategies/ema_macd.py) | Preferred template: inputs, EMA, MACD; understand init/next | Use `run_author.py` |
| [strategies/data_sources.py](../../examples/strategies/data_sources.py) | Eight data sources, saved handles, and derived prices; read the preferred template first | Use `run_author.py` |
| [strategies/cross_signals.py](../../examples/strategies/cross_signals.py) | Crossover composition and current is_* booleans; understand init/next | Use `run_author.py` |
| [strategies/confirmed_events.py](../../examples/strategies/confirmed_events.py) | Composition, confirmed events, patterns, and monthly anchors; understand validity/time alignment | Use `run_author.py` |
| [strategies/ema_inputs.py](../../examples/strategies/ema_inputs.py) | Built-in EMA and inputs; check indicator validity | Use `run_author.py` |
| [strategies/all_inputs.py](../../examples/strategies/all_inputs.py) | All nine inputs, enum/color runtime values, and time/session boundaries | Use `run_author.py` |
| [advanced/native_run.py](../../examples/advanced/native_run.py) | Native runs, statistics/equity/trade tables; direct Python script | Run directly |
| [advanced/composable_strategies.py](../../examples/advanced/composable_strategies.py) | Signal and trailing-stop base classes; understand super call order | Run directly |
| [advanced/multiple_time_frames.py](../../examples/advanced/multiple_time_frames.py) | Built-in daily/weekly RSI; understand resampling, completed periods, and calendar assumptions | Run directly |
| [advanced/parameter_optimization.py](../../examples/advanced/parameter_optimization.py) | Four grid combinations and parameter scores; understand native parameters | Run directly |
| [advanced/machine_learning.py](../../examples/advanced/machine_learning.py) | Feature columns, one-time/rolling training; requires ML and time-series evaluation knowledge | Run directly |

Optimization requires the `optimize` extra; the ML tutorial requires scikit-learn and can take substantially longer. The indicator pages also contain self-contained samples requiring only the installed package.
