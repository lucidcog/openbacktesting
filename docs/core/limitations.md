# Supported boundaries

The engine backtests one asset in one settlement currency per run, with linear margin and contract multiplier 1. `MultiBacktest` runs independent accounts; a Portfolio report describes one run.

- Execution uses OHLC bars. Intrabar path, real liquidity, volume-based partial fills, and realized market slippage cannot be established from OHLC alone. Stops may fill beyond their requested prices after gaps.
- There is no live-trading connection, multi-asset account, currency conversion, futures daily settlement, stock-borrow interest, or funding-fee model.
- Strategy code is ordinary Python. Run code you trust; there is no sandbox. Causal calculations and proper validity checks are the strategy author's responsibility.
- The core package exports plotting data but contains no chart renderer. The optional [Studio](studio/index.md) provides local browser charts and reports. Session inputs and timeframe labels do not infer exchange calendars or resample data automatically.
- Indicator and execution behavior follows this library's documented contracts; Pine/TradingView numerical equivalence is not guaranteed. Windows support has not been fully validated.

[First backtest](quickstart.md) · [Execution rules](guides/trading.md) · [Indicator usage](reference/indicator-api.md)
