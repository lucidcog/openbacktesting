# Run a strategy

For a Python script or notebook, construct `Backtest(data, MyStrategy, ...)` and call `run(...)`. For a reusable strategy file carrying default settings, declare `@backtest(...)` and use `runtime.run(namespace, ...)`.

## Choose an entry point

| Goal | Entry point |
| --- | --- |
| One run with explicit settings | [Backtest.run](../reference/core.md) |
| Apply defaults from a decorated strategy | [runtime.run](../reference/runtime.md) |
| Find a best parameter combination | [Backtest.optimize](../reference/core.md#find-a-parameter-combination) |
| Save and query every candidate | [runtime.optimize](../reference/optimizer.md) |

Both run paths return a pandas Series with statistics and execution tables. Every run gets fresh strategy/account state. `runtime` requires a loaded module namespace, aware market-data index, `DataContext`, and `InstrumentSpec`; the direct `Backtest` path can omit context.

## Keep units explicit

`Backtest(commission=0.002)` and `@backtest(commission_value=0.2)` both mean 0.2% fees, but use different argument units. `buy(percent=20)` means an incremental 20% budget; `order_target_percent(target=0.2)` means a 20% target position. Read the relevant parameter table before transferring values between APIs.

[Full Backtest parameters](../reference/core.md#constructor-parameters) · [Decorator and runtime example](../reference/runtime.md#define-and-run-a-decorated-strategy) · [Results](results.md)
