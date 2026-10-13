# Runnable examples

Start with the [first backtest](../docs/core/quickstart.md), which runs directly from an installed package. The examples here offer longer recipes: `advanced/` files run directly; `strategies/` files declare a strategy and use the example runner to supply data.

## Choose by topic

Use [advanced/optimizer_results.py](advanced/optimizer_results.py) for parameter experiments: retain complete Portfolio results, fix unselected inputs at current values, submit results individually, cancel and resume, reopen offline, and sort by fields.

Choose the topic you need. Bundled GOOG daily and EURUSD hourly data are read locally without downloads. The commands below run from a source checkout.

| Path | Execution category | Recommendation | Topic and prerequisites | Data and extra dependencies |
| --- | --- | --- | --- | --- |
| [advanced/optimizer_results.py](advanced/optimizer_results.py) | Imperative tutorial | Advanced | Select inputs; save complete Portfolios and reopen for sorting | Fixed bundled data; none |
| [strategies/local_value_helpers.py](strategies/local_value_helpers.py) | Author script | Recommended | Tick rounding and per-bar gradients | Fixed host data; none |
| [strategies/local_builtin_indicators.py](strategies/local_builtin_indicators.py) | Author script | Recommended | Conditional VWAP, mode, and five parameter extensions | Fixed host data; none |
| [strategies/closed_trade_statistics.py](strategies/closed_trade_statistics.py) | Author script | Recommended | Partial exits with fees and frozen statistics | Fixed host data; none |
| [strategies/strategy_logs.py](strategies/strategy_logs.py) | Author script | Recommended | Three log levels, nonfatal error logs, explicit exceptions, and end records | Host historical data; none |
| [advanced/strategy_logs.py](advanced/strategy_logs.py) | Imperative tutorial | Advanced | Timestamps, bars, source lines, failure retrieval, reruns, and host sessions | First four GOOG bars; none |
| [strategies/bar_states.py](strategies/bar_states.py) | Author script | Recommended | First-bar callbacks, boundary states, positions, labels, and local validity guards | GOOG; none |
| [strategies/custom_indicators.py](strategies/custom_indicators.py) | Author script | Recommended | Custom functions, two parameter sets, named outputs, and reusable composition | First 120 GOOG bars; none |
| [strategies/plotting.py](strategies/plotting.py) | Author script | Recommended | Color Input, Color/strings, transparency, panes, and per-bar coloring | First 120 GOOG bars; none |
| [advanced/portfolio_report.py](advanced/portfolio_report.py) | Imperative tutorial | Advanced | All report sections, partial-exit identities, MFE/MAE, signals, and frozen JSON | Fixed offline data; none |
| [advanced/plotting_export.py](advanced/plotting_export.py) | Imperative tutorial | Advanced | Color overrides, configuration replay, frozen snapshots, strict JSON, signals, and fills | Trusted author script; none |
| [strategies/trading_lifecycle.py](strategies/trading_lifecycle.py) | Author script | Recommended | Order events, rejection, partial fees, accounts, and end-of-run policies |  |
| [strategies/fractional_sizing.py](strategies/fractional_sizing.py) | Author script | Recommended | Three sizing modes, default overrides, frozen snapshots, named targets, and reduce-only |  |
| [strategies/managed_orders.py](strategies/managed_orders.py) | Author script | Advanced | Expiry, mixed-size OrderRequest OCO, protection, and trailing stops |  |
| [strategies/first_backtest.py](strategies/first_backtest.py) | Author script | Recommended | First backtest: EMA registration, stepwise decisions, and decorator declarations | GOOG; none |
| [advanced/strategy_settings.py](advanced/strategy_settings.py) | Imperative tutorial | Advanced | Five enum categories, flat overrides, JSON versions, and interest recalculation | GOOG and fixed data; none |
| [advanced/chart_context.py](advanced/chart_context.py) | Imperative tutorial | Advanced | Instrument/timeframe injection, chart-local hours, statistical day boundaries, and DST repeated hours | Fixed offline data; none |
| [advanced/run_author.py](advanced/run_author.py) | Imperative tutorial | Advanced | Host loads author scripts and reads results | Example-host data; none |
| [advanced/indicator_reference.py](advanced/indicator_reference.py) | Imperative tutorial | Advanced | Explore by indicator ID and check each channel for validity | GOOG and demonstration extra columns; none |
| [strategies/ema_macd.py](strategies/ema_macd.py) | Author script | Recommended | Preferred template: inputs, EMA, MACD; understand init/next | GOOG; none |
| [strategies/data_sources.py](strategies/data_sources.py) | Author script | Recommended | Eight data sources, saved handles, and derived prices; read the preferred template first | GOOG; none |
| [strategies/cross_signals.py](strategies/cross_signals.py) | Author script | Recommended | Crossover composition and current is_* booleans; understand init/next | GOOG; none |
| [strategies/confirmed_events.py](strategies/confirmed_events.py) | Author script | Advanced | Composition, confirmed events, patterns, and monthly anchors; understand validity/time alignment | GOOG; none |
| [strategies/ema_inputs.py](strategies/ema_inputs.py) | Author script | Recommended | Built-in EMA and inputs; check indicator validity | GOOG; none |
| [strategies/all_inputs.py](strategies/all_inputs.py) | Author script | Recommended | All nine inputs, enum/color runtime values, and time/session boundaries | First 120 GOOG bars; none |
| [advanced/native_run.py](advanced/native_run.py) | Imperative tutorial | Advanced | Native runs, statistics/equity/trade tables; direct Python script | GOOG; none |
| [advanced/composable_strategies.py](advanced/composable_strategies.py) | Imperative tutorial | Advanced | Signal and trailing-stop base classes; understand super call order | GOOG; none |
| [advanced/multiple_time_frames.py](advanced/multiple_time_frames.py) | Imperative tutorial | Advanced | Built-in daily/weekly RSI; understand resampling, completed periods, and calendar assumptions | GOOG; none |
| [advanced/parameter_optimization.py](advanced/parameter_optimization.py) | Imperative tutorial | Advanced | Four grid combinations and parameter scores; understand native parameters | GOOG; SAMBO requires optimize extra |
| [advanced/machine_learning.py](advanced/machine_learning.py) | Imperative tutorial | Research only | Feature columns, one-time/rolling training; requires ML and time-series evaluation knowledge | EURUSD; scikit-learn in test extra |

See [advanced/strategy_settings.py](advanced/strategy_settings.py) for a complete flat-configuration run covering five enum categories, three commission modes, two quantity modes, two slippage modes, JSON overrides, rejection of type changes without values, None clearing, and version 2 envelopes. It retains low-level composite fees and compares inherited interest with explicit zero. `test_flat_backtest_settings.py`, `test_strategy_settings.py`, and `test_examples.py` verify these cases. Quantity budgets do not reserve fees, so actual fills can still fail for insufficient funds.

## Run and verify

In the repository root, install the environment with `uv sync --locked --extra test`, then run the commands below. After unpacking an sdist, start at its package root, run `pip install '.[test]'` in your virtual environment, and replace `uv run --locked python` with `python`. Wheels omit examples; obtain the source or sdist rather than assuming these paths exist after wheel installation.

Run author scripts with this recipe; replace path to select another author script. `runpy` executes trusted local source only and is not a sandbox; runtime does not load source code.

```python
import runpy
from openbacktesting import runtime

path = "examples/strategies/ema_macd.py"
namespace = runpy.run_path(path)
schema = runtime.describe(namespace)  # No backtest has run yet
chart_for = runpy.run_path("examples/advanced/run_author.py")["chart_for"]
chart = chart_for(path)
result = runtime.run(namespace, **chart)
print(schema)
print(result)
```

Execute the recipe in the current Python session. Imperative tutorials calculate only when explicitly run; loading definitions does not backtest, optimize, or train. Run all commands from the package root described above:

```sh
uv run --locked python examples/advanced/strategy_logs.py
uv run --locked python examples/advanced/plotting_export.py
uv run --locked python examples/advanced/run_author.py
uv run --locked python examples/advanced/run_author.py examples/strategies/local_value_helpers.py
uv run --locked python examples/advanced/run_author.py examples/strategies/local_builtin_indicators.py
uv run --locked python examples/advanced/run_author.py examples/strategies/closed_trade_statistics.py
uv run --locked python examples/advanced/run_author.py examples/strategies/all_inputs.py
uv run --locked python examples/advanced/chart_context.py
uv run --locked python examples/advanced/strategy_settings.py
uv run --locked python examples/advanced/indicator_reference.py --indicator ta.macd
uv run --locked python examples/advanced/native_run.py
uv run --locked python examples/advanced/composable_strategies.py
uv run --locked python examples/advanced/multiple_time_frames.py
uv run --locked python examples/advanced/parameter_optimization.py
uv run --locked python examples/advanced/parameter_optimization.py --method sambo
uv run --locked python examples/advanced/machine_learning.py
```

Optimization defaults to four grid combinations; SAMBO uses at most 40 attempts with a fixed seed and requires `python -m pip install '.[optimize]'`. ML runs a random-split classification demonstration and two full backtests, predicts every bar, and retrains every 20 bars. This slow example requires `python -m pip install '.[test]'`. Neither installs dependencies automatically.

## Essential semantics

- `self.open/high/low/close/volume/hl2/hlc3/hlcc4` are stable read-only handles; saved references and slices follow the cursor. `hlcc4=(H+L+2C)/4`. Compose indicators in init; in next, `[-1]` is current and `[-2]` is previous. Prepare data before first accessing a source.
- Each `self.data_index/df` read reflects current visibility; saved pandas objects do not update automatically. `pip` is a price-precision scalar. Array conversions and arithmetic results are not stable handles.
- EMA and daily/weekly RSI use built-in default algorithms. The earlier first-value-seeded EMA and approximate RSI examples were removed; their sequences and backtest results are not current baselines. Weekly data uses Friday right labels and forward filling, without claiming Pine multi-timeframe equivalence.
- Random-split ML accuracy does not establish time-series out-of-sample performance. Label horizons, temporal splits, and gaps require independent evaluation, so the example remains Research only.
- Each docstring explains fees, sizing, and end-of-run liquidation choices. Return output is the calculation for that particular data and configuration.

For maintenance and validation, see the [development guide](../docs/core/development.md).
