# Your first backtest

Run a local backtest on the bundled GOOG historical daily data: buy when price crosses above EMA, close when it crosses below, and read the trades and equity. No market-data download is required.

## 1. Prepare the environment

Run from the repository root:

```sh
uv sync --locked --extra test
```

The current validation environment uses Python 3.12. The paths below belong to the source repository; a standalone wheel installation does not include the examples directory. See [examples](examples.md) for source and sdist installation.

## 2. Define a strategy

The [author source file](../../examples/strategies/first_backtest.py) is a complete runnable definition. Reuse it directly or copy it into your own strategy file:

[Complete source](../../examples/strategies/first_backtest.py)

- `init()` registers EMA; `length=20` sets its calculation period. The latest data and indicator values then advance with the backtest cursor.
- `next()` tests crossings on visible history and submits orders or closes positions. `is_crossover` returns the current boolean value; use `ta.crossover` for historical crossing series.
- `@backtest` stores strategy defaults. Loading this file only defines the strategy; the host supplies market data, timeframe, and instrument specifications and executes it in the next step.

## 3. Run the same strategy

Still at the repository root, run:

```sh
uv run --locked python examples/advanced/run_author.py
```

To select another author example from the index, pass its path as the final argument. `chart_for` supplies only the fixed market-data recipes for these examples; your own host should inject the actual chart. The execution portion of the host's [complete source](../../examples/advanced/run_author.py) is available here:

[Complete source](../../examples/advanced/run_author.py)

Each load creates a new namespace. `runtime.describe` discovers configuration without market data; `runtime.run` accepts host chart context and returns results. Execute only trusted local scripts; this entry point does not provide a sandbox.

## 4. Read the results

The command prints return, trade count, and maximum drawdown, followed by the final rows of the equity curve and trade records:

| Content | Access | Meaning |
| ------- | ------ | ------- |
| Return | `result["Return [%]"]` | Percentage return for this historical data and configuration |
| Trade count | `result["# Trades"]` | Number of closed fragments; this example enables terminal liquidation |
| Maximum drawdown | `result["Max. Drawdown [%]"]` | Maximum percentage drawdown of the equity curve |
| Equity curve | `result["_equity_curve"]` | Equity table aligned to the market-data index |
| Trade records | `result["_trades"]` | Per-trade entry, exit, size, and profit/loss information |

Entry and exit fees use the default `CommissionType.PERCENT` with `commission_value=0.2` (0.2%). Results are calculations for the fixed example, not predictions of future performance. See the [results guide](guides/results.md) for field details.

## Next steps

[Strategy lifecycle](guides/author.md) · [Input declarations](guides/inputs.md) · [EMA reference](reference/indicators/ema.md) · [MACD multiple outputs](reference/indicators/macd.md) · [Running and optimization](guides/runtime.md) · [Complete API](reference/core.md)

`tests/test_examples.py` verifies this example's loading boundary and actual execution. See [current limitations](limitations.md) for further boundaries.
