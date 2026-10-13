# Write a strategy

Start with the complete [EMA crossover strategy](../reference/strategy.md#a-complete-strategy). A strategy subclasses `Strategy`; you provide `init()` and `next()`, and `Backtest` supplies the account and data.

## Decide what belongs where

| Task | Location |
| --- | --- |
| Declare tunable values | Class attributes or [inputs](../reference/inputs.md) |
| Register EMA, RSI, or custom calculations | `init()` |
| Read the current bar and indicator values | `next()` |
| Place or cancel orders; update stops | `next()` |
| React to actual fills | Optional `on_fill(fill)` |
| Inspect order changes | Optional `on_order(event)`; read `event.snapshot` |
| Report termination | Optional `on_finish(summary)` |

`init()` sees complete history, so use trailing formulas and keep indicator handles. `next()` sees the current prefix and is called even when an indicator is invalid. Check `valid[-1]` and check length before reading an earlier bar.

## Work with state

`self.position` is exposure, `self.orders` contains pending orders, and `self.trades` contains open lots. `self.close` is a price series; use `self.close_position()` to exit. Store your own flags or counters on other instance attributes. Input fields and framework data are read-only.

Log decisions with `self.log.info("signal detected")` and read them later with `bt.get_logs()`. Logging a signal does not mean an order filled; inspect fills or `on_fill` for execution facts.

[All Strategy methods and attributes](../reference/strategy.md) · [Orders](../reference/trading.md) · [Composable strategies](../reference/helpers.md)
