# Repository Instructions

- Develop on the `main` branch by default unless the user explicitly specifies otherwise.
- Use English by default for repository code, comments, docstrings, product copy, diagnostics, and general documentation. User-authorized Chinese research and OpenSpec planning artifacts are registered by exact path and content digest in the language exception registry. OpenSpec prose for this project uses Simplified Chinese; structural keywords and contract identifiers retain their original spelling.
- Preserve third-party originals under their recorded upstream file identity. A vendor directory alone does not exempt local additions from project rules.
- Preserve established identifiers and machine-readable contracts when translating prose.

## Project map

- Start with [development and validation](docs/core/development.md) and the [harness guide](docs/core/harness.md).
- Core behavior: `src/openbacktesting/`, `tests/`, [public contracts](docs/core/reference/classification.md).
- Studio: `studio/src/`, `studio/web/src/`, `studio/tests/`, [host protocol](studio/docs/protocol.md).
- Generated references: edit `scripts/docs/` and reviewed catalogs, then use the documented generators.
- Current plans: `openspec/changes/`; completed plans: `openspec/changes/archive/`; [quality evidence](docs/core/harness-quality.md).
- Run `uv run --locked python scripts/verify.py --profile <docs|core|studio|full>`; use `full` when scope is unclear. Never silently regenerate numerical, schema or provenance baselines to pass a check.
