# Core user manual

Define strategies in Python, backtest them on local historical market data, and read trades, equity, and statistics. The current package provides an independent Python core without guaranteeing Pine equivalence.

## Getting started

[Your first backtest →](quickstart.md) starts with fixed offline data, defines a strategy, and runs it through the host.

For API usage, go directly to [backtests and strategies](reference/core.md), the [indicator catalog](reference/indicators/index.md), or [EMA](reference/indicators/ema.md).

## Guides

- **Strategy authoring**: [Lifecycle](guides/author.md) · [Market data](guides/data.md) · [Input declarations](guides/inputs.md) · [Indicator composition](guides/indicators.md)
- **Execution and analysis**: [Running and optimization](guides/runtime.md) · [Orders and trades](guides/trading.md) · [Results](guides/results.md) · [Plot declarations and export](guides/plotting.md)
- **Complete code**: [Runnable examples](examples.md)
- **Parameter experiments**: [Saving and ranking complete Portfolios](guides/optimizer.md)

## API reference

- [Backtests and strategies](reference/core.md)
- [Orders, positions, and trades](reference/trading.md)
- [Strategy composition and helpers](reference/helpers.md)
- [Input declarations and resolution](reference/inputs.md)
- [Host runtime entry points](reference/runtime.md)
- [Indicator handles and computation](reference/indicator-api.md)
- [Plot declarations and export](reference/plotting.md)
- [Color values and presets](reference/colors.md)
- [Portfolio reports and export](reference/portfolio.md)
- [Optimizer result sets](reference/optimizer.md)
- [Indicators by category](reference/indicators/index.md)

## Maintenance and limitations

[Current limitations](limitations.md) · [Compatibility entry points](reference/classification.md) · [Documentation maintenance](development.md) · [Build provenance](build-info.md)
