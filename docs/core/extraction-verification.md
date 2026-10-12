# Extraction acceptance record

Independent package extraction and acceptance completed on 2026-10-12. Validation covered macOS ARM64 and Python `3.12.12`; this record does not imply acceptance of other Python versions or platforms.

## Regression results

- `python -m pytest`: `2877 passed, 1 skipped` in `62.03s`, with `170 warnings`. The skipped item was the complete slow ML example, disabled by default.
- The full suite ran in an independently extracted sdist, using the installed site-packages package and baseline-matching dependencies: `2877 passed, 1 skipped` in `64.88s`, with `170 warnings`. Tests and fixtures did not depend on the original repository or current source directory.
- `python -m openbacktesting.test`: `67` tests, `OK (skipped=1)`, in `13.955s`. The skipped test was Linux-only `TestDocs.test_examples`, with the logged reason `test_examples requires mp.start_method=fork`. The pytest example suite did run.
- After the final example-index adaptation, a separate check of `test_index_and_execution_sets_match` passed.
- `ruff check scripts`, `ruff format --check scripts`, indicator-method generation checks, and API documentation consistency checks passed.

The source regression environment used NumPy `2.5.3`, pandas `3.0.6`, `pandas-ta-classic 0.8.32`, pytest `9.1.1`, SAMBO `1.25.2`, and scikit-learn `1.9.1`. Independent installation resolved NumPy `2.5.4` within the dependency range; other base computation dependencies had the same versions.

The original indicator baseline also compares dependency-version metadata exactly. The unlocked NumPy `2.5.4` environment produced `179` version-field assertion failures, while corresponding numerical assertions passed. The full suite passed after pinning NumPy to the baseline's `2.5.3`. The sdist now includes the project's `uv.lock` for reproduction in the locked environment; assertions and version baselines were not relaxed or changed.

## Distribution and identity

`uv build --no-sources` generated the wheel and sdist. Two separate clean environments installed the wheel directly and installed a rebuilt wheel from an independently extracted sdist, respectively. `PYTHONPATH` and `PYTHONHOME` were cleared, and probes corresponding to `scripts/verify_installation.py` ran with `python -I` from directories without source.

Both installation paths confirmed that the sole new package identity loaded from site-packages. Checks passed for runtime resource access, a minimal backtest, pickle round-trips, spawn transfer, Portfolio saving and reading, optimization-experiment cancellation and recovery, rejection of resume with mismatched identity, and preservation of existing archive content. The base environment returned an explicit dependency error when the optional optimizer was absent; a minimal SAMBO optimization succeeded after installing the artifact's `optimize` extra.

Independent installation exposed a SAMBO top-level import dependency gap: the source test environment supplied scikit-learn/joblib, but the original `optimize` declaration omitted them. The existing test dependency range `scikit-learn>=1.5,<2` has now been added, bringing in joblib; base dependencies and computation algorithms were unchanged.

## Migration consistency and read-only boundaries

The 346 runtime files were compared individually with the direct source snapshot and contained only the agreed identity and path substitutions. Three Base64 pickle fixtures normalized identity strings and updated lengths, frames, and digests. All other opcode bytes were compared individually and remained identical, apart from string encoding and frame encapsulation; historical numerical expectations were not regenerated. Name checking includes the decoded contents of these fixtures.

The source repository commit remained `844bae116047a7b6cf3fe400ab0b98910ccb729b`. Digests were rechecked for 2107 recorded files, including existing core-directory caches, and all matched; the source Git working tree remained clean. All migration, build, test, and installation-verification files were written in the current repository.

`scripts/check_package.py` checked project files, manifests, Python syntax, documentation links, and artifact members. Case-insensitive scans for the former project and package names found zero matches. Documentation, OpenSpec, metadata, and encoded fixtures were all in scope; caches and validation environments were excluded from distribution artifacts.

## Unverified items

Python `3.13/3.14`, other operating systems, the complete slow ML example, and Pine equivalence were not accepted. This work provides local artifacts and does not include uploads, publication to a package registry, or migration of original-project consumers.
