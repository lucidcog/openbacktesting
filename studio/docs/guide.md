# Using OpenBacktesting Studio

For a step-by-step first run with screenshots, see the
[illustrated Studio guide](https://docs.openbacktesting.com/studio/).

Studio is an optional local application. Core-only users keep installing
`openbacktesting` and reading its pandas, Portfolio and PlottingResult exports;
no web server, frontend assets or JavaScript dependencies are added to that package.
The repository contains two independently built Python distributions.

## Installation and launch

For this unreleased source version, first build the frontend as described in the
[maintainer guide](development.md), then install the built distributions into the
same Python 3.12–3.14 environment:

```sh
python -m pip install /path/to/openbacktesting-0.2.0-py3-none-any.whl
python -m pip install /path/to/openbacktesting_studio-0.1.0-py3-none-any.whl
openbacktesting-studio /path/to/strategy-workspace --no-open
```

Open the printed loopback URL, including its one-time fragment token. Studio first
asks you to choose a directory; the CLI path is only the initial location in the
picker, not an automatically loaded workspace. Browse folders or enter an absolute
path, then choose Open directory. Only files and history from that directory load.
The folder button beside Workspace lets you switch after saving edits and finishing
or cancelling active runs. Histories remain in their original workspace directories.
The selected path is saved as `studio.workspace` in browser localStorage and restored
on reload and service restart. An unavailable directory prompts you to choose again. Omit
`--no-open` to open the default browser. The default port is 8765 so browser preferences survive restarts;
`--port 0` requests an ephemeral port. LocalStorage is scoped to the complete origin,
including port, so changing ports or switching between localhost and 127.0.0.1 does
not share the remembered directory. A fixed port fails if another process owns it.
Nothing terminates that other process. `--python /absolute/path/to/python` chooses
the strategy interpreter; install compatible core and Studio packages and the
strategy's dependencies there first. Studio does not install or switch environments.

End users need Python and a browser, not Node, npm, Electron or a CDN connection.
Both the wheel and sdist contain compiled assets, the local Monaco worker and chart
notices. Installing from the sdist uses a Python build backend, not a frontend build.
Once releases are published, `pip install openbacktesting-studio` can resolve its
compatible core dependency. This document does not claim that release is published.

The implementation is verified on macOS. Linux and Windows were not exercised in
this change; filesystem protection currently uses POSIX directory descriptors.

## Edit, configure and run

1. Choose a workspace file. The Code tab preserves each file's unsaved buffer.
   Save writes UTF-8 content back to the actual local file. Ctrl/Cmd+S applies only
   inside the editor. Save failures retain the draft.
2. Open Strategy settings to discover the saved module's single `@backtest` strategy.
   Discovery imports trusted Python in a separate process, without running `init`
   or `next`. First or changed input schemas require review.
3. Configure Inputs, Properties, Data and optional Source roots/resources. Inputs
   use their declared titles, groups, choices, activation rules and defaults.
   Hidden display metadata does not hide form controls. Disabled inputs retain values
   and remain subject to validation. A preset saves JSON without rewriting Python.
4. When Run opens the initial settings review, choose Apply & Run to continue the
   backtest immediately. Opening Strategy settings separately uses Apply to next run
   without starting a backtest. Save & Run saves, snapshots, discovers and validates
   in that order. A conflict, discovery failure or changed schema stops the sequence.
   Every run has immutable configuration; changing the form cannot change a queued run.
5. Review Overview, Performance, List of trades, Settings & Data and Logs.
   Failed runs retain their diagnostics and identify their own run; completed
   reports remain available in history. Out of date identifies results from different source/configuration.

CSV data requires explicit columns, time encoding and timezone for naive timestamps.
Duplicate, unordered, empty or invalid data is rejected without repair. A local loader
must be a named function returning a DataFrame; JSON parameters and declared resources
are captured with the request. Bundled recipes are GOOG daily, BTCUSD monthly and
EURUSD hourly (60 minutes), with an explicit UTC interpretation of their naive fixture
labels. These demonstration recipes do not claim original exchange-timezone metadata.
Timeframe describes supplied bars and never requests resampling. Context timezone can
change strategy calendar semantics and requires a new run; absolute data identity does
not change merely because the same instants are displayed in another timezone.

The chart keeps original bar identities and precise timestamp labels. Signals and
actual fills are separate layers. A bar's detail dialog exposes all its fills, including
multiple fills at one price/time, and both anchor/known-at positions for signals.
Chart picks populate price/time drafts and never start a run. All bars requests a
bounded display projection: OHLCV buckets, order-preserving indicator extrema/gaps,
and event clusters. Open cluster members or locate a trade to read original facts.
Colored aggregate bars use the final color event inside that bucket, not an execution
fact. Excessive gap/crossing complexity produces a range-budget error; narrow the range.

Equity charts show close samples, using the final terminal observation for the drawn
point while retaining both observations in the Close table. Intrabar unordered bounds
are available in Account; they are not connected into an invented path. Metric values,
methods and availability come from Portfolio. Long/short are direction contributions,
not independent accounts. A dash means unavailable, not zero. Money uses the supplied
currency label; Studio does not infer USD.

## History and sharing

History stores each run independently. Selecting a completed run reads its saved
report and chart without rerunning the strategy. Repeated clicks on the selected run
preserve its display; recently viewed artifacts are cached in memory. Read failures
and timeouts show an error rather than an indefinite loading state. Rerun saved snapshot requires locally trusted
source, normalized data, request and the same recorded interpreter; it creates a new
run with a parent link. The loader is not repeated. Imports stay read-only and do not
execute embedded source. External services, credentials and dependencies beyond the
recorded environment are not captured and cannot be promised reproducible.

Export `.obstudio` defaults to reports, chart and provenance. Source, normalized raw
data and logs require explicit selection. Review strategy-controlled input values,
paths and strings before sharing: reports and configuration may themselves contain
sensitive user text. No session token or Cookie is included.

Open an archive or a standalone core Portfolio JSON without a strategy workspace:

```sh
openbacktesting-studio view /path/to/result.obstudio --no-open
openbacktesting-studio view /path/to/portfolio.json --no-open
```

An optional paired JSON object has `portfolio` and `plotting` keys. Studio checks fill
and axis identities before accepting a pair; matching facts are not proof of source
provenance. Archives are size-bounded, checksum-verified data containers, not pickles.
Read-only viewing extracts to a disposable user cache and does not modify the original.

## Execution and storage

This is a trusted local development application, not a Python security sandbox.
Imported strategy and loader code runs with your user permissions, including normal
filesystem and network access. Only use source you trust. Web requests are restricted
to a loopback origin, one-time session exchange, HttpOnly Cookie and write CSRF checks.

`.openbacktesting/studio/` contains SQLite history, snapshots, run artifacts, profiles
and presets. Studio neither edits your `.gitignore` nor stages these files. Add an ignore
rule in your strategy repository if desired. Completed reports are preserved across
restarts; interrupted tasks are marked failed and are never automatically rerun.
Cancellation has a grace period and reclaims the managed process group. The UI only
reports cancelled after the worker exits. Output/log tails are bounded and show truncation.


## Results panel placement

Use the panel icon beside the results tabs to switch between bottom and right
placement. Drag the divider to adjust height or width; focus the divider and use
the corresponding arrow keys for keyboard resizing. The browser remembers the
placement and latest chart/results percentage split, shared by both placements.
Switching preserves the current tab, code draft and chart viewport, and never
starts a backtest. Collapse and reopen the panel without losing the saved split.
Read-only reports provide the same controls.

## Strategy logs

Logs displays timestamped messages with Info, Warning and Error levels instead of a
JSON document. Search supports case sensitivity, whole words and regular expressions;
invalid expressions show an error without losing messages. Combine search with level,
source and starting-date filters, or reset them together. Times use the report timezone;
naive timestamps stay local and messages without timestamps are labeled accordingly.
Messages are paged in groups of 100; truncation and incomplete collection are explicit.

Each available source icon opens the immutable source snapshot at its recorded line.
The bar icon loads a window around that original bar; it does not run Python. Imported
reports without source or chart resources keep their messages but cannot offer those
actions. stdout/stderr are separate sources; stderr alone does not establish severity.
These are saved backtest logs, so no live logging start/stop control is presented.

The interaction reference is TradingView's [Pine logs documentation](https://www.tradingview.com/support/solutions/43000710876-i-d-like-to-learn-more-about-pine-logs/).

## Optimizer

The Optimizer tab follows Code and uses the framework's existing exhaustive optimizer.
Select a strategy and review its settings first. Enable the inputs to search, add
explicit candidates, or choose an inclusive ascending range for int, float or price.
All nine input kinds are supported. Decimal bounds are passed as strings to preserve
the core range semantics. Unselected inputs retain the current configured values.
An optional constraint names a function in the strategy module that receives complete
wire input values and returns bool.

Preview search saves source, normalized data, execution settings and identities, then
shows the dimensions and total before constraints. It imports the strategy and loads
data in a worker but does not execute strategy init/next. Start experiment explicitly
runs the saved plan. Studio shares one execution slot between regular runs and
experiments. Cancel cooperates between trials, with process termination as a fallback.
Resume after cancellation or host interruption uses the frozen source and data; it
checks identities and does not retry previously failed trials. Trial errors remain
visible and do not hide successful combinations.

Ranked results exposes every scalar field from the core result catalogue, including
unit, availability and method metadata. Add columns, multiple sorts and filters using
eq/ne/lt/le/gt/ge/status, then Refresh results. Pages retain the core commit watermark;
Refresh starts a new query that includes newer commits. All trials also shows constraint
skips, failures and attempt numbers. Open report reads the saved complete Portfolio into
the regular report tabs; optimization does not collect plots or logs. Apply inputs copies
a trial into the matching strategy's configuration for review, without running it.

Export database uses a consistent SQLite backup. Imported databases stay queryable and
can open individual reports; they cannot execute or resume source code. Local experiments
are stored under `.openbacktesting/studio/optimizations/` in the selected directory.
