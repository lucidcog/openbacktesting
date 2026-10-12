## Why

The repository currently contains only a README and cannot independently develop, install, or run the backtesting core. Extract the user-designated source repository's `python/core` into this repository, use `openbacktesting` as the sole distribution and import root, and remove dependencies on the original project layout and brand identity.

## What Changes

- Import runtime code, type markers, resources, tests, fixtures, and examples into a root `pyproject.toml` and `src/openbacktesting/` layout; keep the source repository read-only.
- **BREAKING**: Standardize distribution name, import root, module identities, environment variables, branded protocol identifiers, and descriptions on the new name, without former-name aliases or compatibility packages.
- Remove all case variants of the former project and package names across controlled files, files intended for version control, and artifacts. Documentation and OpenSpec are not exempt.
- Import external fixtures actually used by tests and the necessary manual; adapt paths, metadata, and provenance manifests so builds, tests, and usage require neither the source repository nor desktop components or JavaScript tooling.
- Preserve computational semantics for backtests, indicators, orders, statistics, optimization, and data-only plotting; verify completeness with existing regression baselines, resource checks, and standalone installations.
- This stage creates a proposal only. Subsequent implementation excludes registry publication, migration of original consumers, desktop integration, and new backtesting features.

## Capabilities

### New Capabilities

- `standalone-python-package`: Standalone source layout, installation/distribution, complete runtime and development materials, and the read-only source boundary.
- `package-identity`: Unique new package identity, no residual former names, and serialization/persistence compatibility boundaries.
- `extraction-parity`: Auditable migration scope, preserved computational semantics, and independent tests/examples.

### Modified Capabilities

None; this repository has no existing specifications.

## Impact

- Add runtime source, root Python build configuration, tests, examples, necessary documentation, and local verification tools; update the root README.
- Initially retain version `0.2.0`, Python `>=3.12,<3.15`, dependency ranges for NumPy, pandas, and pinned `pandas-ta-classic`, and the `optimize`/`test` extras. Clean-install validation during implementation requires adding the scikit-learn dependency needed by SAMBO to `optimize`, using the existing test range.
- Public import prefixes and branded output identities change. Pickles with old module paths, former protocol identifiers, and resumption of old experiments are outside compatibility guarantees; design and specifications define the boundaries.
- The original repository and its uncommitted changes are unaffected. This proposal does not claim source tests have run or the new package is usable.
