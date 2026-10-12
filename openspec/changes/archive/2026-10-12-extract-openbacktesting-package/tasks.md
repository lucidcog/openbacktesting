## 1. Freeze migration scope and the read-only boundary

- [x] 1.1 Record source revision, working-tree state, imported file digests, and initial target state; deliver snapshot records without former names or machine-absolute paths and verify they can support before/after comparison.
- [x] 1.2 Establish a migration inventory for the core and actual external dependencies, with cache exclusions; verify explicit destinations for runtime code, resources, tests, examples, indicator research fixtures, Portfolio fixtures, and the core manual.

## 2. Establish independent source and build configuration

- [x] 2.1 Copy core source, resources, tests, and examples into `src/openbacktesting/`, `tests/`, and `examples/`; compare the inventory item by item and verify no missing modules, resources, or source-repository links.
- [x] 2.2 Create root `pyproject.toml`, test-isolation configuration, and `.gitignore`, preserving dependency ranges, extras, version, and Python support; verify configuration parses without workspace or source-path dependencies.
- [x] 2.3 Configure wheel/sdist membership; build with `uv build --no-sources` and inspect members to verify runtime resources, all local test/example dependencies in the sdist, and exclusion of caches and virtual environments.

## 3. Unify package and data identity

- [x] 3.1 Update distribution metadata, imports, public object module paths, dynamic resource lookup, dedicated environment variables, log copy, and examples; verify the unique root is `openbacktesting`, without former entry points or fallback logic.
- [x] 3.2 Update indicator backend identities, Portfolio semantic identities, JSON Schema, experiment environment keys, and corresponding test fields; run catalog-consistency and optimization-identity tests to verify definitions, outputs, and validation agree.
- [x] 3.3 Verify new-identity pickle round-trips, spawn transfer, Portfolio save/load, and experiment recovery; reuse probes and add necessary boundary checks to verify mismatched identities reject resumption without damaging existing data.

## 4. Complete tests, documentation, and integrity checks

- [x] 4.1 Import external indicator research records and Portfolio fixtures into local test fixtures and adjust resource paths; run related tests to verify no access to old project levels and retention of original assertions.
- [x] 4.2 Import the necessary core manual and rewrite the README, example index, and development guide with standalone build, install, test, minimal-backtest commands, and historical compatibility boundaries; verify internal links and independence from original tooling.
- [x] 4.3 Update provenance paths, identity text, and target digests, separating historical sources from the direct extraction snapshot; verify complete inventory coverage and digests matching actual files.
- [x] 4.4 Add case-insensitive zero-residual checks over paths and content without writing forbidden names into the rules; scan controlled/pending files and wheel/sdist artifacts to verify no matches in docs, OpenSpec, manifests, or metadata.

## 5. Complete standalone and regression acceptance

- [x] 5.1 Install the `test` extra in an isolated environment inside this repository, run `python -m pytest` and `python -m openbacktesting.test`, and cover existing examples/probes; retain numerical baselines and record repairs and explicit skips without weakening assertions.
- [x] 5.2 Install the wheel and an sdist-rebuilt wheel in separate clean environments, remove source-path injection, and run imports, resource access, minimal backtests, serialization, spawn, and optimization persistence outside source directories; verify imports resolve inside installed environments.
- [x] 5.3 Verify base-install backtesting and clear missing-optimizer errors, then minimal optimization with `optimize`; confirm dependency groups remain functional after migration.
- [x] 5.4 Rebuild final artifacts and recheck names, migration inventory, and source state; record commands, Python/dependency versions, platform, and unverified items. Mark extraction complete only after required acceptance passes and no writes to the source repository.
