# Implementation and verification

The standalone extraction is complete. The sole distribution and import identity is `openbacktesting`, version `0.2.0`. The original repository was not modified; public computational behavior was preserved, and historical compatibility boundaries follow the design.

## Actual results

- Root Python project, source, resources, tests, examples, core manual, and independent verification tools are present.
- Existing pytest regressions: `2877 passed, 1 skipped`; package self-tests: `67` tests, `OK (skipped=1)`.
- Full pytest from an independently extracted sdist, using the installed package and baseline dependency versions, also reported `2877 passed, 1 skipped`. The sdist carries the project lock file to reproduce dependency-metadata baselines.
- Direct wheel installation and sdist-rebuilt installation passed resource, backtest, pickle, spawn, optimization-persistence, and base/optional-dependency checks.
- Changes to 346 runtime files were limited to identities and paths; opcode bytes in three encoded pickle baselines remained unchanged except string encoding and frame packaging.
- Rechecks of 2107 source file digests, the source revision, and Git working state agreed.

## Implementation corrections

Clean installation revealed that SAMBO's top-level import requires scikit-learn/joblib, a dependency absent from the source `optimize` extra and concealed by the `test` environment. Added `scikit-learn>=1.5,<2` to `optimize` using the existing test range; base dependencies, algorithms, and numerical baselines were unchanged.

Documentation tooling was adapted to directly readable Markdown, and original-project commands, historical links, and resource paths were repaired. Website-build configuration was not imported; the manifest records its exclusion reason.

## Validation evidence

See the [acceptance record](../../../../docs/core/extraction-verification.md) for environments, commands, results, and unverified scope. Validation used macOS ARM64 and Python `3.12.12`; other Python versions, platforms, and full slow ML examples were not accepted. Repository files and wheel/sdist artifacts passed name and integrity scans. No registry publication occurred.
