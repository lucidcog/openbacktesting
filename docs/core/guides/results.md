# Read backtest results

`Backtest.run`, `run_inputs`, and `runtime.run` return a pandas Series. Start with summary statistics, then inspect trades and the equity curve to understand the run.

## Read common fields

Continue from the [first backtest](../quickstart.md):

```python
print(result[["Return [%]", "# Trades", "Win Rate [%]", "Max. Drawdown [%]"]])
trades = result["_trades"]
equity = result["_equity_curve"]
print(trades[["EntryTime", "ExitTime", "Size", "PnL"]].tail())
print(equity.tail())
```

| Statistic | Interpretation |
| --- | --- |
| `Return [%]` | Account return in percentage points; 5 means 5%. Includes open holdings valued at termination. |
| `Equity Final [$]`, `Equity Peak [$]` | Final and maximum account equity in settlement-currency units. |
| `# Trades` | Closed trade fragments, including partial exits; not submitted orders or necessarily distinct lots. |
| `# Closed Lots` | Count of fully closed lots. |
| `Win Rate [%]` | Winning share of closed trade fragments in percentage points. |
| `Max. Drawdown [%]` | Largest equity decline from a previous peak; a negative percentage. |
| `Sharpe Ratio`, `Sortino Ratio`, `Calmar Ratio` | Risk-adjusted statistics; undefined inputs may produce NaN. |
| `Commissions [$]` | Actual charged commissions. |
| `Start`, `End`, `Duration` | Recorded input period. Inspect report execution information for early termination. |

## Inspect execution tables

| Result key | What you learn |
| --- | --- |
| `_equity_curve` | Equity/drawdown path indexed by market bars. |
| `_trades` | Closed fragments with entry/exit times, prices, signed Size, net PnL, Commission, and ReturnPct. |
| `_open_trades` | Lots still open at termination, remaining entry fees, and unrealized profit/loss. |
| `_orders` | All requests and latest states, including canceled/rejected/expired requests. |
| `_order_events` | Status and trigger transitions. |
| `_fills` | Each actual execution: order ID, time, side, quantity, price, and fee. |
| `_order_sizing` | Original size mode/budget and the quantity frozen at submission. |
| `_trade_allocations` | How fills opened or closed particular lots. |
| `_positions`, `_account_curve` | Exposure and balance/equity/margin observations. |
| `_final_account` | Final account values. |
| `_strategy` | Completed strategy instance for inspecting your own attributes. |

`_trades.ReturnPct` is a fraction: 0.05 means 5%, unlike summary keys ending in `[%]`. A run can show nonzero return with zero closed trades when it still holds a position. Use `end_policy="close_at_last_close"` if you want final holdings liquidated rather than simply valued.

## Save a report

```python
import json
from openbacktesting.portfolio import export_result

report = export_result(result)
text = json.dumps(report, allow_nan=False)
```

The [Portfolio module](../reference/portfolio.md) provides a complete plain-value report independent of later edits or runs. Its metric objects include value, unit, method/status information; inspect status before treating a missing value as zero. Portfolio fractions and native percentage statistics use different units.

Native underscore-prefixed tables are useful in Python. For saved/application reports, use Portfolio export. For visual data, use the separate [plotting export](../reference/plotting.md).

## Interpret limitations

OHLC cannot establish the true intrabar path or market liquidity. A backtest report reflects the configured execution model. Profit ratios may be undefined without losses, and calendar statistics need sufficient history. Read metric status and [trading rules](trading.md) before comparing results.

[Portfolio fields](../reference/portfolio.md) · [Saved experiments](../reference/optimizer.md) · [User manual](../index.md)
