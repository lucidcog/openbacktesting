## Context

See [proposal.md](proposal.md) for motivation and scope. Read-only inspection on 2026-10-12 found:

- The target contained only a README. The source working tree was clean at revision `844bae116047a7b6cf3fe400ab0b98910ccb729b`; implementation must reconfirm the snapshot rather than assume the checkout never changes.
- Source `python/core/pyproject.toml` already used Hatchling, version `0.2.0`, wheel/sdist configuration, and two extras, supporting reuse of an independent package layout.
- `test_indicator_expansion.py` read external indicator research records, and `test_optimizer.py` read a root Portfolio fixture. Copying only the core directory would not make tests independent.
- The README depended on the external `docs/core` manual. Provenance records held target paths/digests; indicator/Portfolio catalogs, JSON Schema, runtime, and experiment identities embedded the former identity.
- Numerical baselines, serialization, and multiprocessing probes existed. This inspection read source only; tests had not run.

## Goals / Non-Goals

**Goals:** Define extraction with an explicit file scope and identity changes while preserving computational semantics; build and validate independently from the target repository.

**Non-Goals:** No algorithm refactor, dependency upgrade, chart renderer, old-identity compatibility layer, PyPI publication, or source-repository modifications. A documentation website is outside delivery.

## Decisions

### 1. Use a root standalone Python project

The target contains `pyproject.toml`, `src/openbacktesting/`, `tests/`, `examples/`, `docs/`, and required `scripts/`. Preserve module boundaries, public exports, dependency ranges, and initial version `0.2.0`; keep `__version__` consistent with distribution metadata. Reusing the version only reduces migration variables and does not permit mixing old-identity artifacts.

Clean-install validation found that SAMBO `1.25.2` imports scikit-learn and joblib at top level but declares them as optional dependencies. The source `test` extra concealed that gap. Add `scikit-learn>=1.5,<2` to `optimize`, matching the existing test range; its dependencies install joblib. Base runtime dependencies and original version ranges remain unchanged. This configuration repair is necessary for standalone optimizer installation.

The sdist carries this project's `uv.lock` solely to reproduce the exact development/test environment; ordinary pip installation still resolves declared dependency ranges. Indicator baselines also check dependency-version metadata, so unlocked runs must not justify rewriting or weakening them.

Do not retain the `python/core` shell, workspace source dependencies, absolute paths, symbolic links, or editable dependencies targeting the source checkout: they conceal independence failures. The wheel includes runtime source and all runtime resources; the sdist also includes tests, examples, necessary docs, fixtures, and local verification inputs.

### 2. Define a complete migration inventory

Include core source, CSV/JSON resources, `py.typed`, tests, examples, and test-isolation configuration. Exclude caches, virtual environments, build artifacts, and source Git metadata.

Also import core-related Markdown/resources from `docs/core`, repair relative links, and remove inapplicable desktop/whole-repository development entries. Do not copy unrelated research or general repository docs. Import the actually consumed `docs/research/engine-indicator-coverage-disposition.json` and root `tests/fixtures/portfolio.json` as local target fixtures, adjusting paths while retaining assertions. Prefer `importlib.resources` for runtime resources.

Reuse and update provenance target paths/digests, retain supported source digests and third-party declarations, and add the direct extraction snapshot and mappings. Use normalized source identifiers and paths relative to the package root, without former names or machine-absolute paths. Record historical upstream provenance separately from the direct copy source; an upstream revision in an old manifest must not be presented as the extraction checkout revision.

### 3. Replace identity across string contracts

The sole distribution and import root is `openbacktesting`, display name `OpenBacktesting`, and dedicated environment prefix `OPENBACKTESTING_`. Branded Portfolio method/semantic identity is `openbacktesting_portfolio_v1`, and the local indicator backend identity is `openbacktesting.numpy`. Preserve unbranded fields and numerical definitions.

Update dynamic imports, resource lookup, object module paths, error/log text, examples, test snapshots, schema constants, distribution keys in experiment environments, documentation, and build configuration together. Maintain the extracted JSON Schema locally without depending on the source repository's protocol generator.

Provide no old-name package, import alias, environment fallback, or dual protocol identity. Old-module-path pickles do not load automatically; Portfolio data with former semantic identifiers is not guaranteed to load directly; old experiments cannot resume under the new identity. Users should rerun to generate new-identity data. New-identity data must save, load, and restore normally; generic data structures unrelated to identity keep their contracts.

An explicit compatibility break is necessary because zero residual names cannot coexist with old-name compatibility logic. Replacing imports alone misses protocol and execution-environment identities and is insufficient for completion.

### 4. Include documentation in zero-residual checks

Scan paths and contents of controlled and non-ignored pending files, matching the two forbidden names without regard to case. Include source, comments, tests, baselines, manifests, README, and OpenSpec. Check wheel/sdist member paths, contents, and distribution metadata.

Reconstruct forbidden terms from character-code configuration so the checker does not introduce their literal names. Matches must fail; excluding checked files is not an acceptable workaround. Internal Git history and local environments/caches are outside deliverables. Do not rewrite history, and do not package these local outputs.

### 5. Distinguish identity changes from computational changes in validation

First check the migration inventory, forbidden-name absence, repository path closure, resources, documentation links, and build metadata. Then run imported pytest and package self-tests, retaining numerical baselines and adjusting only identity/path fields. Do not regenerate numerical expectations or remove assertions to conceal differences.

Create clean virtual environments inside this repository's isolated verification directory. Install the wheel and an sdist-rebuilt wheel separately, then run imports, resource reads, minimal backtests, new-identity pickle round-trips, multiprocessing spawn, and optimizer persistence outside source directories. Remove source injection such as `PYTHONPATH` and verify imports resolve inside installed environments. Check base installation and `optimize` separately, use `test` for the full suite, retain explicit slow-example opt-ins, and report unexecuted cases.

Validation requires no source-repository access. If comparison probes must run source code, use an isolated copy inside the target repository so pytest, interpreters, and examples cannot create caches or outputs in the source checkout. Reuse existing tests and add only missing standalone-install/identity-boundary checks.

## Risks / Trade-offs

- [Hidden external dependency] -> Rebuild from a standalone sdist and execute outside source directories to verify closure.
- [Branded identity changes affect historical consumers] -> Declare the identity break, exclude former archive/pickle compatibility guarantees, and test new-identity round-trips.
- [Bulk replacement changes algorithms or numerical snapshots] -> Review diffs, retain numerical baselines, and identify allowed identity-field changes separately.
- [Source checkout changes during implementation] -> Record revision, state, and imported digests at the start and recheck at the end; report external changes without reverting others' work.
- [Manual/manifests increase scope] -> Import only core material and actual dependencies needed for closure, excluding the whole repository's tooling.
- [Artifacts omit test resources] -> Inspect wheel and sdist membership separately rather than relying on workspace access to conceal omissions.

## Migration Plan

Record the source snapshot and target state, copy into this repository, unify identities and paths, complete local dependencies/docs, update manifests, and perform static checks, regressions, and independent artifact validation. All writes, builds, and test outputs remain inside this repository.

Rollback only files added or changed by this operation in the target repository. Do not operate on the source checkout or overwrite preexisting user changes. Report installability after implementation completes; this proposal stage neither builds nor publishes the package.
