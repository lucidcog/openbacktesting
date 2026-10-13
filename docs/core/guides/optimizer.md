# Compare and save parameter runs

Choose `Backtest.optimize` when you want the highest-scoring result. Choose `runtime.optimize` when you want a persistent report for every candidate and later ranking/filtering.

## Best-run search

`bt.optimize(length=[10, 20, 40], maximize="Return [%]", return_heatmap=True)` returns `(best_result, scores)`. Candidate keys are Python field names. Install the optimize extra; see [the complete example](../reference/core.md#find-a-parameter-combination).

## Saved experiment

[Run the complete saved-experiment script](../reference/optimizer.md#run-and-query-an-experiment). It declares inputs, supplies a search keyed by display titles, writes each Portfolio to SQLite, and queries the results.

1. Choose `Values([...])` or `Range(start, stop, step)` for each title.
2. Supply the loaded strategy, data/context/instrument, a new local output path, and source/dependency hashes.
3. Call `runtime.optimize`, then inspect the returned `ExperimentResult`.
4. Reopen with `open_result(path)` for read-only queries without the original strategy.

Use `fields()` to discover sortable metrics and units. `query` returns selected scalars; `load_portfolio(trial_id)` returns the full report. Sorting does not rerun the strategy. Use `backup(destination)` while a run is writing rather than copying only its database file.

Resume with `runtime.resume_optimization` and the original experiment ID plus matching inputs, source, data, and settings. Changed material needs a new experiment. Saved experiments retain Portfolios, not plot/log history.

[Parameters, queries, and resume](../reference/optimizer.md) · [Portfolio report](../reference/portfolio.md)
