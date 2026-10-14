---
title: Studio — compare parameters
description: Preview parameter combinations, run experiments, and compare or export saved trial reports.
---

# Compare parameters

Open `ema_inputs.py` from your example workspace and review its [strategy settings](first-backtest.md), then open **Optimizer**, immediately after **Code**:

1. In **Search setup**, enable Fast period. Keep its first value at `12`, then use **Add Fast period value** twice to enter `13` and `14` in separate fields; keep Slow period at 26. Enable Allow shorting and use **Add Allow shorting value** to include both `false` and `true`. This creates six combinations.
2. Click **Preview search** to capture source, settings, and normalized data and inspect the planned combinations. Preview can import strategy code and load data, but does not execute `init()` or `next()`.
3. Click **Start experiment**. You can cancel and resume using the frozen inputs; regular runs and optimization share one execution slot.
4. In **Ranked results**, choose columns, add sorts or filters, and click **Refresh results**. **All trials** includes skipped and failed combinations.
5. Use **Open report** for the saved Portfolio, or **Apply inputs** to review a trial's parameters for the next regular run.

[![Completed six-combination EMA parameter experiment with saved metrics and trial actions](../_static/studio/optimizer-results.png)](../_static/studio/optimizer-results.png)

Optimization currently saves Portfolio reports, **not per-trial plots or logs**. Apply a trial's inputs and run a regular backtest when you want its chart. **Export database** creates a consistent SQLite backup; **Import experiment** opens it for querying and reports, without executing or resuming imported code. See [parameter experiments](../guides/optimizer.md) for core search and query semantics.
