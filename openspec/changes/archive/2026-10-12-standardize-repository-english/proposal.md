## Why

The repository currently mixes English identifiers with Chinese documentation, docstrings, generated references, and diagnostics. Establishing English as the default language makes development and package usage consistent while preserving intentional multilingual content.

## What Changes

- Establish the repository language policy in root `AGENTS.md` (created during this proposal) and reinforce it in the OpenSpec project configuration.
- Translate existing project-authored comments, docstrings, documentation, examples, metadata, diagnostic messages, and descriptive JSON text into English, including current and archived OpenSpec documents.
- Translate generator templates and their source metadata before regenerating indicator methods, API references, indicator pages, and the search index.
- Preserve intentional multilingual or localized copy and fixtures that exercise it; Chinese-only default labels do not qualify automatically.
- **BREAKING**: Translate project-authored exception, warning, and CLI message text into English. Consumers matching Chinese messages must update; exception types and failure conditions remain unchanged.
- Adapt text-dependent assertions and descriptive fixture fields without changing numerical baselines, public identifiers, signatures, serialized field names, or computational behavior. Keep provenance records accurate after text changes.
- Add a narrow static language check with explicit, reviewable exemptions to prevent accidental Chinese prose from returning; include repository instructions and OpenSpec records in the sdist so the checker has a complete local scope.

## Capabilities

### New Capabilities

- `repository-language-policy`: English defaults across repository content and distribution artifacts, controlled multilingual exceptions, reproducible English generation, and static enforcement.

### Modified Capabilities

- `extraction-parity`: Permit declared language-only changes to project-authored messages and text-dependent assertions while preserving numerical and behavioral parity and source provenance.

## Impact

- Affected areas: `src/openbacktesting/`, `tests/`, `examples/`, `docs/core/`, root configuration and README, `scripts/`, provenance manifests, and `openspec/` including its archive.
- Generation sources include `scripts/generate_indicator_api.py`, `scripts/core_docs.py`, indicator catalog descriptions, `docs/core/api-manifest.json`, and `docs/core/indicator-notes.json`.
- Package name, version, dependencies, public API signatures, result schemas, numerical fixtures, and multilingual input handling remain stable. Default presentation text and diagnostics change language.
- Validation uses static checks, generation drift checks, existing Python regressions, and package integrity checks. No browser workflow is needed.
