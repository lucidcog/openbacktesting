# Prepare and read market data

Pass one asset's chronological OHLC bars as a pandas DataFrame. Exact columns are `Open`, `High`, `Low`, `Close`, and optional `Volume`. Prices must be finite and positive; index values must be unique and increasing. See [CSV loading, timezones, and instrument rules](../reference/data.md) for complete examples.

## Choose the right access

| Need | Use |
| --- | --- |
| Current close | `self.close[-1]` |
| Previous close | `self.close[-2]`, after checking at least two bars exist |
| Current timestamp | `self.data_index[-1]` |
| Current zero-based position | `self.bar_index` |
| Full currently visible table | `self.df` |
| An additional column | `self.data.MyColumn` |
| A pandas snapshot of a handle | `self.close.s` |

In `init()`, history is complete. In `next()`, reads stop at the current bar. Saved handles continue following that cursor; saved pandas/NumPy snapshots do not. Preprocess before registering indicators and do not mutate market prices during the run.

`self.hl2`, `hlc3`, and `hlcc4` supply `(H+L)/2`, `(H+L+C)/3`, and `(H+L+2*C)/4`. Quantity steps and price ticks come from `InstrumentSpec`, not from the data's apparent decimal precision.

[Data reference](../reference/data.md) · [Indicator inputs](../reference/indicator-api.md#bind-inputs-and-read-outputs)
