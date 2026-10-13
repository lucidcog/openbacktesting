---
title: Python Backtesting Framework and Strategy Guide
description: Build and test Python trading strategies with OpenBacktesting. Learn historical backtesting, technical indicators, order execution, optimization, and portfolio reports.
---

# OpenBacktesting: Python backtesting framework

Write a Python strategy, run it on historical OHLC data, and inspect trades and performance. This manual is for people using the framework.

**[Run your first backtest →](quickstart.md)** — a complete script using bundled data, with no data download or application integration required.

## Choose your next task

| I want to… | Read |
| --- | --- |
| Load market data or set asset rules | [Data, timeframes, and instruments](reference/data.md) |
| Define entry and exit logic | [Strategy](reference/strategy.md) |
| Set cash, fees, and execution timing | [Backtest](reference/core.md) |
| Place, cancel, protect, or close trades | [Orders, Position, and Trade](reference/trading.md) · [Account and events](reference/events.md) |
| Calculate or compose indicators | [Indicator usage](reference/indicator-api.md) · [Full catalog](reference/indicators/index.md) |
| Make strategy parameters configurable | [Inputs](reference/inputs.md) |
| Read return, equity, and trade details | [Results](guides/results.md) · [Portfolio export](reference/portfolio.md) |
| Compare parameter values | [Best-run optimization](reference/core.md#find-a-parameter-combination) · [Saved experiments](reference/optimizer.md) |
| Add visuals or colors | [Plotting declarations](reference/plotting.md) · [Color](reference/colors.md) |
| Reuse signal/trailing strategies or resample data | [Helpers](reference/helpers.md) |
| Run a strategy file with declared defaults | [Decorator and runtime](reference/runtime.md) |

## How the pieces fit

1. Prepare a pandas DataFrame containing one asset's bars.
2. Define a `Strategy`: register indicators in `init()`, read the current bar and place orders in `next()`.
3. Construct `Backtest(data, MyStrategy, ...)` and call `.run(...)`.
4. Read statistics and execution tables, or export a Portfolio report.

`Order` tracks a request, `Trade` tracks one filled lot, and `Position` summarizes open exposure. An order normally executes at the next bar's open. Indicator values can be invalid during initial history; your strategy checks them before acting.

## Tutorials and scope

[First backtest](quickstart.md) · [Trading rules](guides/trading.md) · [Indicator recipes](guides/indicators.md) · [Runnable examples](examples.md)

The engine models one asset and one settlement currency per run. It exports plotting data but includes no chart renderer or live-trading connection. See [supported boundaries](limitations.md) before interpreting results.
