# Current boundaries

## Semantic boundaries

The current trading model has one asset, one settlement currency, and linear margin. Default execution is at the next bar's open; same_close is a single close phase on the current bar, and end_policy controls termination. Ambiguous protective orders follow deterministic policies and record diagnostics; this does not imply knowledge of the true intrabar path. next runs from the first bar, and indicator validity does not gate execution; strategies must check valid before consuming indicators.

Future development will build indicators, Series/state, broker, and multiple-timeframe capabilities individually through a semantic SDK owned by the project. The Python library provides no code sandbox; run only trusted code. Windows, full Pine comparisons, live execution, portfolio accounts, and desktop installation without a development environment have not been accepted.

Volume fillers, multi-asset scheduling, futures contract multipliers/daily settlement, stock-borrow interest, funding fees, exchange sessions, and live-trading guarantees are unsupported. OHLC alone cannot validate actual slippage or liquidity; a stop-loss budget does not guarantee a maximum loss.
