# Strategy authors and lifecycle

After inputs are declared, the host can scan selected inputs through [parameter experiments](optimizer.md), keeping other values fixed at the current configuration. Experiment entry points collect neither logs nor plots; strategies should avoid mutable module globals or external state shared across runs.

## User script: strategy and backtest declarations

Authors declare default backtest settings for a strategy class through `@backtest(...)`. Loading a script only defines the strategy; the framework injects market data, timeframe, timezone, and instrument specifications from the current chart before creating an independent backtest session:

[Complete source](../../../examples/strategies/ema_macd.py)

Each author module must contain exactly one concrete `Strategy` subclass defined in that module and decorated directly. Aliases are not counted twice; imported classes and derived classes without their own decoration are not entry points. The decorator preserves the original class identity. Explicitly redecorated derived classes use their own setting defaults rather than inheriting the parent's declaration.

`@backtest` accepts account, cost, execution-policy, statistical-benchmark, and default-quantity settings, like strategy default properties; `inputs` defines algorithm parameters. `self.timeframe` provides this run's chart timeframe and cannot be overridden through class fields, inputs, or runtime parameters. See [host execution](runtime.md) for the complete boundary.

`init()` can access full data and precompute indicators; `next()` sees progressively revealed history, with the latest price at `self.close[-1]`. Legacy `self.data.Close[-1]` remains available. Registering an indicator does not make it a Pine implementation; precomputation must not use future information.

## Flat backtest settings

All `@backtest()` arguments are keyword-only; categorical options use enums imported from `openbacktesting`. Author entry points reject bare strings, dictionaries, and `Commission`, `DefaultOrderSize`, or `Slippage` configuration objects; those models remain available for low-level `Backtest`.

```python
from openbacktesting import CommissionType, QuantityType, Strategy, backtest

@backtest(
    commission_type=CommissionType.PERCENT,
    commission_value=0.2,
    default_qty_type=QuantityType.PERCENT_OF_EQUITY,
    default_qty_value=10,
)
class MyStrategy(Strategy):
    def init(self):
        pass

    def next(self):
        if len(self.data) == 2:
            self.buy()
```

This commission is 0.2% of executed notional. Default quantity converts 10% of request-time equity using Close. `self.buy()` uses the default quantity, `self.buy(qty=1)` specifies asset units, `self.buy(amount=500)` specifies notional, and `self.buy(percent=20)` uses 20% of equity. The three explicit sizing arguments are mutually exclusive and override defaults. Reduce-only orders require explicit qty; each OCO member must specify one sizing mode and does not inherit defaults. Quantity budgets reserve no fees and guarantee no future execution; insufficiently small budgets raise errors.

| Parameter | Default | Meaning and range |
| --------- | ------- | ----------------- |
| `cash` | `10000` | Initial account amount, finite and greater than 0 |
| `spread` | `0.0` | Fractional spread, [0,1); 0.001 means 0.1% |
| `commission_type` | `CommissionType.PERCENT` | Commission mode; see below |
| `commission_value` | `0.0` | Percentage [-10,10) or nonnegative account amount |
| `risk_free_rate` | `0.0` | Fractional annual risk-free rate for statistics, (-1,1); 0.02 means 2% |
| `default_qty_type` | `QuantityType.FIXED` | Fixed asset quantity or equity percentage |
| `default_qty_value` | `None` | None disables default quantity; fixed quantity >0; equity percentage (0,100] |
| `margin` | `1.0` | Margin ratio, (0,1]; 0.5 permits up to 2x margin leverage |
| `execution_timing` | `ExecutionTiming.NEXT_OPEN` | Process new unconditional market orders on the next bar or current close |
| `slippage_type` | `SlippageType.BPS` | Fixed price distance or basis points |
| `slippage_value` | `0.0` | Nonnegative slippage distance; 0 disables slippage |
| `allow_short` | `True` | Permit new shorts; strict bool |
| `max_gross_exposure` | `None` | Optional gross notional/equity limit, finite and >0 |
| `hedging` | `False` | Permit concurrent long and short lots; strict bool |
| `exclusive_orders` | `False` | Retain the exclusive-order policy; strict bool |
| `end_policy` | `EndPolicy.MARK_TO_MARKET` | Terminal valuation or liquidation of actual holdings |

All numeric values must be finite; bool cannot stand in for a number. Only `default_qty_value` and `max_gross_exposure` allow None.

| Enum member | JSON value | Units / behavior |
| ----------- | ---------- | ---------------- |
| `CommissionType.PERCENT` | `percent` | Percentage of executed notional; 0.2 = 0.2%; negatives denote rebates |
| `CommissionType.CASH_PER_ORDER` | `cash_per_order` | Fixed account amount per actual Fill, not per order registration |
| `CommissionType.CASH_PER_CONTRACT` | `cash_per_contract` | Account amount per actual asset unit; contract multiplier is 1 |
| `QuantityType.FIXED` | `fixed` | Fixed asset quantity |
| `QuantityType.PERCENT_OF_EQUITY` | `percent_of_equity` | Request-time equity percentage; 10 = 10% |
| `SlippageType.FIXED` | `fixed` | Fixed price distance |
| `SlippageType.BPS` | `bps` | Basis points; 1 = 0.01% |
| `ExecutionTiming.NEXT_OPEN` | `next_open` | Process no earlier than the next bar |
| `ExecutionTiming.SAME_CLOSE` | `same_close` | Process new unconditional market orders at the current close; conditional and protective orders retain causal restrictions |
| `EndPolicy.MARK_TO_MARKET` | `mark_to_market` | Cancel pending orders and retain marked-to-market holdings |
| `EndPolicy.CLOSE_AT_LAST_CLOSE` | `close_at_last_close` | Cancel pending orders, then liquidate actual holdings at the final Close with costs |

Only commission PERCENT and quantity PERCENT_OF_EQUITY use percentage units; spread, margin, risk_free_rate, and max_gross_exposure retain their fractional/multiple units. Authors select one commission mode at a time; composite fees or callables use low-level Backtest. See the [settings tutorial](../../../examples/advanced/strategy_settings.py) for complete execution and overrides, and the [trading guide](trading.md) for order boundaries.

## Chart time

Read `self.data_index[-1]` in `next()` for the current bar's timezone-aware timestamp in the chart timezone; `self.data.index` and `self.df.index` have the same interpretation. `.hour`, `.date()`, and `.weekday()` can be used directly for local calendar conditions. Conversion occurs before strategy construction and init without changing visible scope. For example, underlying `01:00 UTC` becomes `09:00+08:00` on a Shanghai chart, and the strategy reads hour `9` directly.

Rerun after changing chart timezone; logic depending on local time may produce different results. During New York's daylight-saving fallback, the two `01:30` timestamps have different offsets and remain distinct bars; do not strip timezones and deduplicate by wall-clock time. This is the bar timestamp, not system execution time, and does not infer exchange openings or monthly-bar boundaries. Fixed market-time logic can explicitly call `tz_convert("America/New_York")`.

The runnable [chart-context tutorial](../../../examples/advanced/chart_context.py) demonstrates timezone injection, orders based on local hours, repeated hours, and statistics grouped by chart-local days.

## Strategy logs

Use `self.log.info(message)`, `warning(message)`, or `error(message)` in author callbacks. Each accepts only a string and returns None. f-strings are supported; Chinese text, empty strings, newlines, and duplicate messages are preserved verbatim. error records a level only; explicitly raise to terminate execution. Complete author example:

[Complete source](../../../examples/strategies/strategy_logs.py)

Logs automatically record UTC system time, the current input bar timestamp, zero-based `bar_index`, and the actual call's file and one-based source line. init/on_finish have no current bar, so bar fields are None; on_start binds bar 0. Logs from helpers point to the helper's actual logging line; they neither record the full call stack nor read source text. File and line are both None when location is unavailable.

`log` is reserved: it cannot be a class field, method, Input field, or native parameter, and `self.log` cannot be assigned or deleted. An Input display title may still be “log”. Logging is unsupported in constructors, outside callbacks, or after execution; author-thread/asynchronous writes are not guaranteed. Logs are independent of plotting switches and global Python logging configuration; they capture neither print/warnings automatically nor write to the terminal. See [log results](results.md#strategy-logs) for consumption and fields.
