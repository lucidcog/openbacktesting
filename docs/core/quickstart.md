# Your first backtest

This example buys one unit when a fast EMA crosses above a slow EMA, closes it on the reverse crossing, and prints performance and trades. It uses bundled historical GOOG data.

## 1. Install

Use Python 3.12–3.14. From a terminal, install the source repository into your environment:

```sh
git clone https://github.com/lucidcog/openbacktesting.git
cd openbacktesting
python -m pip install .
```

If you already use this checkout with uv, `uv sync --locked` is sufficient. An installed package includes the bundled sample data; the script below can run outside the repository.

## 2. Save and run this script

Save as `first_backtest.py`, then run `python first_backtest.py` (or `uv run --locked python first_backtest.py` in the checkout).

```python
from openbacktesting import Backtest, Strategy
from openbacktesting.test import GOOG


class EmaCross(Strategy):
    fast_length = 10
    slow_length = 30

    def init(self):
        self.fast = self.ta.ema(self.close, length=self.fast_length)
        self.slow = self.ta.ema(self.close, length=self.slow_length)

    def next(self):
        if len(self.close) < 2:
            return
        if not (self.fast.valid[-2:].all() and self.slow.valid[-2:].all()):
            return
        if self.ta.is_crossover(self.fast, self.slow) and not self.position:
            self.buy(qty=1)
        elif self.ta.is_crossunder(self.fast, self.slow) and self.position:
            self.position.close()


bt = Backtest(GOOG, EmaCross, cash=10_000, commission=0.002,
              end_policy="close_at_last_close")
result = bt.run()
print(result[["Return [%]", "# Trades", "Max. Drawdown [%]"]])
print(result["_trades"][["EntryTime", "ExitTime", "Size", "PnL"]].tail())
print(result["_equity_curve"].tail())
```

## 3. Understand the run

- `init()` registers both indicators once. In `next()`, their handles reveal only history through the current bar.
- `next()` runs from the first bar. The guards wait for two valid observations before comparing crossings.
- `buy(qty=1)` requests one asset unit. The default timing executes eligible market orders at the next open; `position.close()` likewise submits exit orders.
- `commission=0.002` charges 0.2% on executions. `close_at_last_close` closes remaining holdings at the final close; the default policy instead leaves them open and valued at that price.
- `run()` returns a pandas Series. Percentage statistics use percentage points; `# Trades` counts closed fragments.

## 4. Change one thing

Run the same strategy with another slow period using `bt.run(slow_length=50)`. To use your own prices, replace `GOOG` with a DataFrame following the [market-data requirements](reference/data.md). To expose validated settings, replace class defaults with [inputs](reference/inputs.md).

## Next steps

[Strategy lifecycle](reference/strategy.md) · [All Backtest options](reference/core.md) · [Orders and stops](reference/trading.md) · [Indicator catalog](reference/indicators/index.md) · [Read results](guides/results.md)
