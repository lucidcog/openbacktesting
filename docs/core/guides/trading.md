# Understand order execution

A submitted `Order` is a request, a filled `Trade` is a lot, and `Position` aggregates the currently open lots. The [trading reference](../reference/trading.md) contains order parameters and examples for cancellation, stops, OCO, and target positions.

## From signal to fill

1. Existing eligible orders are processed against the new bar.
2. Order/fill notifications are delivered.
3. `next()` reads the visible history and submits new requests.
4. With the default `next_open` timing, new requests can execute no earlier than the following bar.

`same_close` processes new unconditional market orders from `next()` at that close. It does not let new limit/protective orders use the bar's already-observed High/Low. Orders submitted in event callbacks are not matched recursively.

## Manage risk in the correct units

| Expression | Meaning |
| --- | --- |
| `buy(qty=2)` | Add two asset units |
| `buy(amount=2000)` | Add a notional budget of 2,000 settlement-currency units |
| `buy(percent=20)` | Add a budget of 20% of request-time equity |
| `order_target_percent(target=0.2)` | Target a net position worth 20% of request-time equity |
| `trade.set_trailing_stop(percent=0.05)` | Trail by a 5% distance |
| `trade.close(portion=0.5)` | Submit an exit for half the lot |

Budgets convert into fixed quantities at submission and exclude fees. A gap can cause rejection or an execution value different from that budget. `reduce_only=True` requires explicit quantity and cannot open new exposure.

## Protection and OHLC ambiguity

`sl` and `tp` are absolute prices. Initial protection activates after entry. For conditional or same-close entries, it cannot use earlier High/Low information from the same bar. If a bar reaches both SL and TP and the path is unknown, SL takes precedence and an ambiguity is recorded. Stop execution can gap beyond the stop price.

Native trailing stops ratchet after favorable price movement for later bars. Partial exits cancel/rebuild protection for the remaining quantity. Canceling protection does not close the position.

## End of data

The default `mark_to_market` policy cancels pending orders and retains open lots valued at the last close. `close_at_last_close` instead liquidates existing holdings and charges costs. It does not fabricate fills for final-bar entries that never reached an eligible execution phase.

Read `result["_fills"]` for executions, `result["_order_events"]` for status changes, and `result["_open_trades"]` for remaining exposure. Signal counts and order counts are not trade counts.

[All trading classes and methods](../reference/trading.md) · [Backtest options](../reference/core.md) · [Results](results.md)
