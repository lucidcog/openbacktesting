# Studio protocol version 1

The host namespace is `/api/v1`. A client must negotiate the exact supported
protocol version before operations. The container, data profile and preset each
use independent integer `schemaVersion: 1` fields. Unknown major versions and
unknown required container features are rejected. Optional future fields require
an explicit schema update; current requests reject extra fields.

The Pydantic models in `src/openbacktesting_studio/protocol` are authoritative.
Run `python scripts/export_schemas.py` from the Studio directory to generate the
JSON schemas packaged next to the models. Requests use strict JSON types, finite
numbers, canonical relative paths and explicit timezone/timeframe/instrument
information. OS path containment checks are additionally required by the host.

- `DataProfile` selects sample, CSV or a registered local loader; maps source
  columns and time encoding; preserves explicit timezone, timeframe, instrument,
  inclusive start/end and declared resources. It never requests implicit resampling.
- `Preset` stores its own version and a nested, unchanged core input request
  (`schemaVersion`, `schemaHash`, title-keyed `values`) plus sparse settings.
- `RunRequest` binds a source revision, roots/resources, input request, data profile,
  settings, idempotency key and optional parent run. Loading fixes the actual data
  identity before execution; submitting an identifier never proves reproducibility.
- `RunManifest` stores immutable run identity, status, provenance and artifact
  path/size/SHA-256 records. Duplicate paths and unknown required features fail.
  Portfolio and PlottingResult remain unmodified core exports with separate versions.
- `FileWrite` requires the disk base revision; conflicts preserve both versions.
- `ErrorResponse` carries code, message, field errors, details and request ID.
  Messages use English; user text is never translated or treated as HTML.

## Workspace selection

The CLI starts without an active workspace. Authenticated `GET /directories?path=...`
returns only direct child directories; `PUT /workspace` with `{ "path": "..." }`
selects the root. Both use the existing session boundary, and writes require Origin
and CSRF validation. Capabilities include `workspace`, `workspaceId` and
`suggestedWorkspace`. Clients send `X-Studio-Workspace` on scoped requests; stale
identities receive `WorkspaceChanged`. Switching drains in-flight operations and
refuses active or queued runs. Read-only viewers expose neither selection endpoint.

## Report row locations

Paginated report rows include `rows`, `total`, `offset`, `limit` and `fillBars`.
The optional `fillBars` map resolves fill IDs on the current page to canonical
bar indices from the saved portfolio facts. It is separate from `rows`: allocation
records remain unchanged core exports. Clients must not attempt chart navigation
when neither the record nor this map provides a valid bar index.

## Optimization experiments

Workspace routes use the same session, origin, CSRF and workspace-identity checks.
The read-only viewer does not install execution or optimization routes.

| Endpoint under `/api/v1` | Operation |
| --- | --- |
| `GET /optimizations` | Saved experiment summaries |
| `POST /optimizations` | Capture `OptimizationRequest` and asynchronously prepare a plan |
| `GET /optimizations/{id}` | Plan, lifecycle status, counts and bounded worker diagnostics |
| `POST /optimizations/{id}/start` | Start or resume the frozen experiment |
| `POST /optimizations/{id}/cancel` | Request cooperative cancellation and bounded process shutdown |
| `GET /optimizations/{id}/fields` | Core scalar catalogue |
| `POST /optimizations/{id}/query` | `OptimizationQuery`: columns, ordered sorts, typed filters and opaque cursor |
| `GET /optimizations/{id}/trials?offset=0&limit=100` | All visited combinations and attempt diagnostics |
| `GET /optimizations/{id}/trials/{trial}/portfolio` | Complete saved Portfolio |
| `POST /optimizations/{id}/trials/{trial}/open` | Idempotently materialize a report-only run from the saved trial |
| `GET /optimizations/{id}/export` | Consistent SQLite backup |
| `POST /optimizations/import` | Import SQLite bytes, maximum 512 MiB, query-only |

`OptimizationRequest` embeds the normal run source/inputs/settings/data plus a search
mapping and optional constraint function name. The host captures source before launching
a fresh worker. Planning stores normalized market data; execution and resume read that
snapshot. No request, plan or database includes session credentials. Imported results do
not contain the source/data needed to resume. Query errors, stale cursors and unavailable
trial reports return a structured 422 response; concurrent workspace execution returns 409.
