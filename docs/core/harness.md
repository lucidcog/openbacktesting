# Repository verification harness

The harness connects repository knowledge, existing checks, real Studio journeys and maintenance feedback. Change authors run the relevant profile and repair failures; maintainers own boundary exceptions, compatibility decisions and CI policy.

## Find the source of truth

| Change | Read first | Validation |
| --- | --- | --- |
| Core execution, orders or results | [Development](development.md), [trading](guides/trading.md), [results](guides/results.md) | `core`; use `full` for distribution changes |
| Studio host or interface | [Studio workflow](studio/index.md), [protocol](../../studio/docs/protocol.md), [development](development.md) | `studio` |
| Documentation or generated references | [Development](development.md#documentation-and-generated-interfaces), `scripts/docs/` templates | `docs` |
| Cross-domain, dependencies or unclear scope | [Development](development.md), [quality evidence](harness-quality.md) | `full` |

OpenSpec proposals and task lists under `openspec/changes/` describe planned work until completion is recorded; completed changes are retained under `openspec/changes/archive/`. Do not restore previously deleted archives to satisfy stale links. General documentation and diagnostics use English; authorized Chinese plans use exact path and digest entries in `scripts/language-exceptions.json`.

## Run a profile

Install uv and Python 3.12–3.14, then from the repository root run:

```sh
uv run --locked python scripts/verify.py --profile core
uv run --locked python scripts/verify.py --profile docs
uv run --locked python scripts/verify.py --profile studio
uv run --locked python scripts/verify.py --profile full
```

Omitting `--profile` selects `full`. `--list` prints selected check IDs without executing them. The single catalogue is `scripts/harness_checks.py`. `HARNESS_PYTHON` selects an installed or uv-managed Python version for both locked environments. Root and Studio environments remain separate. Preparation synchronizes locked dependencies; it never updates lockfiles. Studio builds its web assets before synchronizing its Python environment.

`docs` and `core` need no Node or browser. `studio` and `full` additionally need Node 22.12+ and the development browser. After installing frontend dependencies, install it explicitly:

```sh
npm --prefix studio/web ci --ignore-scripts
npm --prefix studio/web exec -- playwright install chromium
```

Use `playwright install --with-deps chromium` on Linux CI when OS libraries are required. Missing dependencies fail with preparation guidance; a missing browser is never counted as a passed journey. Package versions come from metadata. Optional slow ML examples remain excluded unless `OPENBACKTESTING_RUN_SLOW_EXAMPLES=1`; reports list this exclusion.

## Read the result and repair failures

Each attempt writes `.verification/harness/<run-id>/result.json`, `summary.md` and bounded, redacted logs. JSON includes the commit and dirty state, tool versions, lock digests, profile and per-check commands, duration, exit code and evidence paths. `passed`, `failed`, `error`, `blocked` and `cancelled` are different states. All required checks must pass for exit code zero. A retry is a new attempt, not a replacement for an earlier failure.

Fix the reported cause, run the narrow check while iterating, then rerun the selected profile. Never update a numerical baseline, schema or provenance manifest merely to make a check pass. Checks may write ignored build and evidence outputs, but must not rewrite tracked sources or approved generated files. Unexpected changes fail verification and remain available for review; the harness never resets existing edits.

For schema drift, first review the model change; run `studio/.venv/bin/python studio/scripts/export_schemas.py` only when intentionally regenerating. `--check` compares without writing. Other generated references must be edited through their source templates and generators described in the development guide.

## Studio evidence

Three real browser journeys cover editing and running a strategy, chart/report navigation with export and read-only reopening, and a failed run followed by repair. They use local deterministic data, the actual Python host and worker, dynamic loopback ports, and isolated temporary workspaces. They do not replace the chart, editor or API with mocks. No user browser profile is used.

Dependencies may be downloaded during setup; runtime fixtures reject external connections. The fixture is test instrumentation, not a sandbox for untrusted code. Failures save bounded screenshots and redacted UI, request and process diagnostics. Raw traces are not uploaded. Processes and temporary workspaces are reclaimed even after failure. Existing HTTP and component tests remain responsible for the wider protocol and component matrix.

## Architecture and maintenance

Architecture checks protect core independence, reviewed lower-layer dependencies and exact Studio internal adapters. Exceptions require a reason, owner role and removal condition; unused exceptions fail. Dynamic imports that cannot be statically resolved are explicitly reported as coverage limits. Behavioral regression tests remain authoritative for numerical and event semantics.

Run `uv run --locked python scripts/doc_gardening.py` after preparing the root and Studio environments. It reuses read-only checks and emits JSON plus candidate repair notes. `--previous <maintenance.json>` compares finding identities; without prior evidence it marks history as unknown. It does not rewrite files, push commits, create PRs or merge. Preserve local reports when comparing later runs. Maintainers turn recurring findings into a targeted regression or rule and update [quality evidence](harness-quality.md).

GitHub Actions workflows are currently removed. Verification and maintenance run locally through the commands above; archived plans describe the earlier CI design.
