# Implementation and verification

Completed `standardize-repository-english` on 2026-10-12. Repository code explanations, documentation, generated references, default examples, package metadata, and project-authored diagnostics now use English. Intentional multilingual content remains unchanged under exact, justified exceptions.

## Delivered behavior

- Root `AGENTS.md` and OpenSpec configuration define the English default, multilingual-copy exception, and preservation of established identifiers.
- Source comments, docstrings, diagnostic text, descriptive JSON, examples, handwritten documentation, and current/archived OpenSpec prose are English. Indicator methods, API references, indicator pages, and search metadata were regenerated from translated sources.
- `scripts/check_language.py` is integrated with `scripts/check_package.py`. It checks literal and escaped Python/JSON prose, valid embedded JSON, repository files, and distribution members without executing source code.
- The exception registry binds Python fixtures to qualified class/function names and exact values/counts, rejects unused or overused rules, and preserves historical OpenSpec matching identifiers. No directory-wide language exemption exists.
- Both provenance manifests have accurate final target digests and language-adaptation notes. Original source revisions, retrieval facts, source hashes, mappings, and counts remain intact.
- The sdist includes the checker, registry, repository instructions, and OpenSpec records. This closes the exemption scope and allows strict checks directly after extraction without the OpenSpec CLI.

## Compatibility and invariants

Project-authored Chinese diagnostics now use English. Consumers matching old messages must update their expectations. Default example titles and edited strategy source can change schema or execution fingerprints; identity validation remains enforced.

Public API signatures, exception classes and rejection conditions, formulas, numerical parameters, result/schema field names, numerical baselines, and historical pickle payloads remain unchanged. Nineteen existing JSON files were independently checked for unchanged structure and numerical/boolean values; historical encoded payloads and their digests were checked byte-for-byte. Source AST comparisons preserve non-text executable structure.

Frozen pickle objects still contain their original localized names/titles. Their tests assert those original values under narrow exemptions rather than rewriting payloads. A historical localized-title schema hash and the new English-title hash are both explicitly verified. Other retained fixtures cover multilingual logs, enum values, and order tags.

## Actual validation

Environment: macOS 26.5 ARM64, Python `3.12.12`, NumPy `2.5.3`, pandas `3.0.6`, pandas-ta-classic `0.8.32`, SAMBO `1.25.2`, scikit-learn `1.9.1`, pytest `9.1.1`, Ruff `0.17.0`, using the repository lock file.

| Check | Actual result |
| --- | --- |
| `uv run --locked ruff check src tests examples scripts conftest.py` | Passed |
| `uv run --locked python scripts/generate_indicator_api.py --check` | Passed |
| `uv run --locked python scripts/core_docs.py --check` | Passed |
| `uv run --locked python -m pytest` | `2890 passed, 1 skipped`; 171 warnings; 60.75 seconds |
| `uv run --locked python -m openbacktesting.test` | 67 tests; `OK (skipped=1)` |
| Language-checker regression tests | 13 passed, including exact selectors, stale exceptions, escaped/nested strings, and wheel/sdist scope |
| `uv build --no-sources` | Wheel and sdist built successfully |
| Package integrity checks on the repository, wheel, and sdist | Passed: language, forbidden names, target digests, resources, syntax, and local links |
| Packaged checker executed directly from an independently extracted sdist | Passed without an OpenSpec CLI dependency |
| Wheel/extracted-sdist runtime smoke checks | Package loaded from each artifact path; resource access, public-object pickle round-trip, and a one-trade minimal backtest passed with locked dependencies |
| `openspec validate --all --strict` | 5 items passed, 0 failed |
| `git diff --check` | Passed |

The full pytest run initially identified six integration failures from translated message assertions and historical localized pickle expectations. These were repaired without weakening numerical assertions, rewriting payloads, or bypassing identity checks; the final full run above passes.

The pytest skip is the explicitly opt-in full ML example. The existing package self-test skip requires multiprocessing start method `fork`; the validation environment used its normal configuration. Other platforms/Python versions and the optional full ML run were not validated. Artifact smoke checks use existing locked dependencies and are not a fresh dependency-resolution test.

Local command logs are retained under `.verification/english-*`; these local outputs are excluded from distribution artifacts. The change was archived on 2026-10-12. Main-spec synchronization was skipped at the user's request.
