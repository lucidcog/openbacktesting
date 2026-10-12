# Core development and validation

Public behavior changes require corresponding updates to guides, API references, runnable examples, and validation. Runtime source lives under `src/openbacktesting/`, divided into data, broker, strategy, simulation, portfolio, optimizer, and indicators; the package exports its public entry points.

## Environment and commands

Run from the current repository root:

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
uv run --locked python scripts/generate_indicator_api.py --check
uv run --locked python scripts/core_docs.py --check
uv build --no-sources
uv run --locked python scripts/check_package.py --artifact dist/openbacktesting-0.2.0-py3-none-any.whl --artifact dist/openbacktesting-0.2.0.tar.gz
```

`uv.lock` fixes this repository's validation environment and is distributed with the sdist. Independent installations resolve dependencies from `pyproject.toml` and do not require the lockfile. After extracting the sdist, establish the environment with `uv sync --locked --extra test`, then run the same Python test commands. Historical baselines compare dependency-version fields exactly, so full regression requires the locked environment; identity differences from other dependency versions must not be treated as numerical regressions. Enable the complete slow ML examples explicitly with `OPENBACKTESTING_RUN_SLOW_EXAMPLES=1`; they do not run by default.

In addition to SAMBO, the `optimize` extra declares scikit-learn, which brings in joblib. The current SAMBO top-level import requires these dependencies; a base backtesting installation does not add them.

## Documentation and generated interfaces

The manual is directly readable Markdown and requires no website build. The public API manifest is `api-manifest.json`; indicator names, purposes, and example relationships are in `indicator-notes.json`. After changing interfaces or the catalog, regenerate and check:

```sh
uv run --locked python scripts/generate_indicator_api.py
uv run --locked python scripts/core_docs.py
uv run --locked python scripts/check_package.py
```

`generate_indicator_api.py` generates indicator methods from the fixed catalog. `core_docs.py` generates API signatures, docstrings, and indicator references from installed objects and the catalog. Handwritten guides are not overwritten. Machine checks confirm structural consistency; prose semantics still require review.

## Distribution integrity

The wheel includes runtime source, `py.typed`, indicator and Portfolio catalogs, result schemas, and built-in CSV data. The sdist additionally includes tests, fixtures, examples, the manual, provenance manifests, and local checking tools. In an independent environment, verify from a working directory without source that the loaded package belongs to site-packages, and exercise a minimal backtest, resource access, pickle, spawn, and optimization-result saving and recovery.

`check_package.py` scans project paths and content with case-insensitive naming rules, covering documentation, tests, OpenSpec, and artifact metadata. It also checks file manifests, Python syntax, documentation links, and unintended Chinese prose, including decoded JSON and Python strings. Exact multilingual exceptions require an English rationale; missing, changed, or unused exceptions fail validation. The same language checks apply to wheel and sdist content. Deliverable files must not be excluded to hide matches.

## Provenance and behavioral boundaries

The [historical source manifest](../../source-manifest.json) preserves earlier upstream evidence; the [extraction manifest](../../extraction-manifest.json) records the direct source snapshot and path mappings. Source paths are normalized to the new identity, source digests still identify original bytes, and target digests identify current content.

The extraction migration preserves API signatures, computed values, and event order while adapting identity and paths. The declared English standardization additionally translates project-authored presentation text and diagnostics; consumers matching former Chinese messages must update, while exception types and rejection conditions remain unchanged. Pickles referencing old module paths do not load automatically; old-brand semantic archives are not guaranteed to be directly readable, and old experiments cannot resume under a new execution identity. Data with the new identity supports normal saving, reading, and recovery. See [current limitations](limitations.md) for usage boundaries.

New capabilities must extend the example index and actual execution validation; syntax checks alone are insufficient for delivery. Internal refactoring must demonstrate unchanged public behavior. This repository does not depend on desktop components, a parent workspace, or a JavaScript toolchain.

The source distribution includes repository instructions and OpenSpec records so the language exception registry has the same complete file scope when checked after extraction. Running the Python integrity checker does not require the OpenSpec CLI.
