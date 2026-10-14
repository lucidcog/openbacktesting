---
title: Studio — run your first strategy
description: Run the bundled EMA strategy and configure inputs, execution properties, and market data.
---

# Run your first strategy

After [installing Studio](installation.md) and [choosing your workspace](workspace.md), run the bundled example.

Choose the example directory offered by the Studio launcher, then search for and open **ema_inputs.py**. The installer keeps these examples in `~/.local/share/openbacktesting-studio/examples`; in a source checkout, use `examples/strategies`. This example declares a single `@backtest` strategy with configurable EMA periods and order quantity. A script that only calls `Backtest(...).run()` is not automatically a Studio strategy; see [decorator and runtime](../reference/runtime.md).

1. Click **Run**. The first run opens **Strategy settings** for review.
2. In **Inputs**, keep Fast period **12**, Slow period **26**, Trade quantity **1**, and Allow shorting off. Keep the fast period below the slow period.
3. In **Properties**, review cash, commissions, sizing, and execution behavior.
4. In **Data**, keep **Bundled sample → GOOG**, UTC, and day × 1. No market-data download is needed.
5. Click **Apply & Run**. Wait for the run to become **succeeded** and the report to appear.

[![EMA strategy inputs grouped into Moving average and Trades, with Apply & Run](../_static/studio/strategy-inputs.png)](../_static/studio/strategy-inputs.png)

[![Data settings using bundled GOOG bars, UTC, and a daily timeframe](../_static/studio/data-settings.png)](../_static/studio/data-settings.png)

For your own data, select **Workspace CSV** and specify its path, time column, OHLCV columns, time encoding, and source timezone for naive timestamps. **Local Python loader** accepts a function that returns a DataFrame. See [market data](../guides/data.md) for DataFrame and timestamp requirements. Changing the timeframe label does not resample prices.
