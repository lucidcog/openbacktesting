# Use indicators in a strategy

Register formulas in `init()` through `self.ta`. Consume their current values in `next()` only after checking the selected channel's validity. The [complete indicator strategy](../reference/indicator-api.md#single-and-multiple-outputs) demonstrates EMA, MACD, and composition.

## Common recipes

| Goal | In `init()` |
| --- | --- |
| EMA of Close | `self.average = self.ta.ema(self.close, length=20)` |
| RSI | `self.rsi = self.ta.rsi(length=14)` |
| MACD channels | `self.macd = self.ta.macd(fast=12, slow=26, signal=9)` |
| Smooth a derived channel | `self.smooth = self.ta.sma(self.macd.histogram, length=3)` |
| Custom rolling calculation | `self.mean = self.ind(lambda s: s.rolling(20).mean(), self.close.s)` |
| Historical crossing signals | `self.cross = self.ta.crossover(self.fast, self.slow)` |

During `next()`, `self.average[-1]` is the latest value and `self.average.valid[-1]` says whether it can be consumed. Multi-output indicators require a channel, e.g. `self.macd.histogram`. Use `self.ta.is_crossover(a, b)` for a current boolean rather than registering a series inside `next()`.

## Avoid future information

The full input is available in `init()`. Use causal calculations; negative shifts or saving a future scalar can leak data. Indicator handles constrain visible history during `next()` but cannot repair a noncausal function. Arrays created by arithmetic or `.s` conversions are snapshots; retain handles for dynamic reads.

Confirmed pivots are published after the right-hand window finishes. Anchored formulas require an explicit 0/1 anchor series. Pattern score zero can mean a valid non-event; validity is separate from direction or strength.

## Find a formula

Every [catalog page](../reference/indicators/index.md) includes a complete script, parameter descriptions, and output names. Start with [EMA](../reference/indicators/ema.md), [RSI](../reference/indicators/rsi.md), [ATR](../reference/indicators/atr.md), or [Bollinger Bands](../reference/indicators/bbands.md).

[All shared arguments and handle operations](../reference/indicator-api.md) · [Custom indicators](../reference/strategy.md#register-custom-calculations)
