# Parameter experiments and local Portfolios

`runtime.optimize()` scans selected inputs while fixing the remaining current values, committing each complete Portfolio to a local SQLite result database immediately after generation. It returns `ExperimentResult` for reopening, filtering, and ranking; there is no objective function or automatic best-parameter rerun. Legacy `Backtest.optimize()` remains a separate entry point returning the best statistics.

## Starting and search domains

See the [parameter-experiment tutorial](../../../examples/advanced/optimizer_results.py) for complete code. Run:

```sh
uv run --locked python examples/advanced/optimizer_results.py --output /tmp/optimizer-demo.db
```

Output must be a new local file; use `runtime.resume_optimization()` for an existing experiment. The first version stores one experiment per database and does not support network filesystems. The database is portable after normal closure; to copy during execution, use `result.backup(destination)` rather than copying only the main file, which may still have a WAL.

search keys are unique input titles; request contains current `schemaVersion/schemaHash/values`. Omitting request uses declaration defaults, not overrides from the previous run. Every combination's complete effective values are saved.

| Search domain | Usage and boundaries |
| ------------- | -------------------- |
| `Values([1, 2])` | Finite candidates of existing input types; enums accept members or wire member names |
| `Range(5, 25, 5)` | Ascending int grid with a positive step; rejects bool and fractions |
| `Range("0.1", "0.3", "0.1")` | float/price uses finite decimal strings or integers, avoiding binary floats as exact range inputs |

stop is included only if it lies on the grid; 0…1/0.3 ends at 0.9, and start=stop yields one value. Each dimension permits at most 100,000 values, and the combination count cannot exceed the signed 64-bit integer limit. Disk or runtime constraints may apply much earlier; these limits do not imply that such large searches can finish. Empty domains, empty searches, invalid candidates, and duplicates are rejected before execution without silent sampling. active affects presentation only; declared step does not constrain search steps.

An optional constraint receives complete **wire values**, must return bool, and requires a stable constraint_id. False records a skip; an exception aborts. The valid total remains unknown until every candidate is checked. The function is not stored; resume must supply a constraint with the same digest. Return preferences belong in query filters rather than parameter constraints.

## Execution identity and recovery

The host declares SHA256 identities of actually loaded source and local dependencies through `ExecutionIdentity(strategy_sha256, dependencies_sha256)`. The engine additionally identifies market-data columns/index/types/content, settings, timezone, instrument, and Python/dependency versions; only numeric, boolean, and time columns are accepted, not object columns. The example hashes its own source; real hosts must include relevant local modules rather than treating a mutable path as content identity.

Market data and settings are frozen at startup, and each combination receives a new strategy and account. Module globals, external files/network access, and arbitrary RNGs are not strongly isolated. Matching identity does not prove arbitrary strategy determinism and is not a security sandbox.

Resume supplies namespace, current request/settings, data/context/instrument, and identity again; the framework reads search domains from the database and verifies the plan. Only undispatched/interrupted combinations are filled in; successful, skipped, and failed combinations are not automatically rerun. Changed materials or versions require a new experiment. Missing source or market data does not prevent read-only inspection, but execution cannot continue.

cancel is a no-argument callable. After it returns True, the next combination is not dispatched; an in-flight combination may finish and be saved. Arbitrary infinite Python loops cannot be guaranteed to stop. Committed combinations remain readable after forced termination; uncommitted attempts are marked interrupted on resume. A crash after computation but before commit may cause that combination to rerun.

## Portfolio-only retention

This entry point always disables log and plot collection, without attachment switches. The database retains complete public Portfolios, inputs, configuration/version identity, status, and brief errors. It does not store Strategy, pickle, stdout, raw market data, or complete source text. Ordinary backtest logging and plotting behavior is unchanged.

Zero-trade, open-position-only, and normal-bankruptcy runs all retain reports. Success means the report transaction committed, not profitability or reaching the end of market data; inspect Portfolio complete/terminationReason for the latter. Strategy/export failures are recorded and execution continues; storage failures stop execution. `OptimizationError` includes path, experiment_id, and last known committed count, and states when the error status could not be written to disk.

Progress callbacks run after successful commits. Callback exceptions do not undo committed results but stop subsequent execution. The result database is the source of progress facts.

## Queries and complete reports

`open_result(path)` does not load a strategy. `info()` returns categorized counts and the plan; `trials(limit, offset)` browses live states of visited combinations; `load_portfolio(trial_id)` validates and reads a complete report. `fields()` provides paths, types, units, status, method, and suggested sorting direction suggestedDirection.

- `query(order_by=["summary.all.totalReturn.value"])` defaults to descending returns; `summary.all.maxDrawdownFraction.value` and positive drawdowns in analysis default to ascending, while legacy negative drawdowns default to descending. Explicit `(path, "asc"/"desc")` overrides this; multiple keys follow list order.
- filters are `(path, op, value)`, with eq/ne/lt/le/gt/ge/status operators; filtering does not delete reports.
- Missing/null values sort last. A null+unbounded profit factor with no losses is not treated as infinity; approximate flags are retained. Mixed units/methods cannot be ranked together; integers and encoded nanoseconds are compared exactly.
- Paths use dot separators; dots and backslashes in original keys must be escaped, for example `extensions.legacy.Max\. Drawdown [%].value`. Arrays/objects cannot be sorted directly.
- limit is 1…1000. A cursor fixes the query and commit watermark, so new commits do not enter subsequent pages; query again without a cursor to refresh. Ties sort by ordinal.

Queries return paginated parameters and selected scalars; complete reports are read separately. Saving projects all object scalars without traversing arrays. Queries neither rerun strategies nor rewrite historical reports using current statistics code. The first version supports storage format 1 and Portfolio 1.0.0; unknown versions and corruption are explicitly rejected without automatic migration.

## Validation boundaries

Unit tests are in `tests/test_optimizer.py`; `test_examples.py` actually executes the example. Run `uv run --locked python -m pytest tests/test_optimizer.py` to verify commits, recovery, process locks, queries, and identity boundaries. The first version is serial; this extraction makes no cross-machine capacity or hardware power-loss guarantees.

## Package identity and existing results

Execution-environment identity records the actually installed `openbacktesting` version. New-identity experiments support reopening, querying, ranking, and reading Portfolios. Historical archives with old-brand semantic identifiers are not guaranteed to be directly readable; old experiments cannot resume under the new identity and must be rerun to generate data. Rejecting resume with mismatched identity does not rewrite committed results.
