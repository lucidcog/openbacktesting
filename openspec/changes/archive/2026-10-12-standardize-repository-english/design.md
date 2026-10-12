## Context

See `proposal.md` for the motivation and scope. The initial scan found 715 non-ignored files containing Han characters, including 328 under `src/openbacktesting/` and 278 under `docs/core/`. This is an inventory signal, not proof that every match needs translation.

The repository is a standalone Python package. Two generators publish indicator methods and documentation. `scripts/core_docs.py` also emits search UI copy and JSON metadata; its generated-file discovery relies on a Chinese marker. The package checker verifies local links, resources, source syntax, and the `targetSha256` fields in both provenance manifests. Tests match Chinese exceptions and consume Chinese example categories, input titles, and descriptive fixtures. Some logging and input tests deliberately exercise multilingual text.

`AGENTS.md` now states the English default as the immediate deliverable. Existing parity requirements only permit identity and path adaptations, so the delta explicitly allows language-only changes without weakening computational guarantees. The two original requirement names in the delta's `FROM` entries remain exact historical OpenSpec matching identifiers. Existing scenario names were preserved during proposal validation, then translated in both the main spec and delta after synchronization; current scenario names and all new prose are English.

## Goals / Non-Goals

**Goals:**

- Translate default project prose consistently and keep regeneration deterministic.
- Preserve numerical and behavioral evidence while making text changes auditable.
- Make multilingual exceptions small and visible and prevent unintended Chinese prose from returning.

**Non-Goals:**

- Introduce a localization framework, translate user data, or require ASCII-only content.
- Rename public APIs, change calculations, alter dependency versions, or replace historical numerical and pickle baselines.
- Add browser infrastructure or publish a documentation website.

## Decisions

### 1. Translate by semantic role

Inventory comments, docstrings, human-facing strings, descriptive JSON fields, and documents separately from identifiers, protocol keys, numbers, source hashes, and opaque baseline payloads. Translate root documentation and configuration, source prose, tests and probes, examples, metadata, and all OpenSpec prose, including the archive. Keep paths and explicit link anchors stable.

Only actual localized or multilingual copy and fixtures that exercise it receive text exemptions. Chinese-only example labels become English; intentional Unicode round-trip inputs remain. Established OpenSpec source requirement names are machine-readable migration identifiers, not new default prose.

Alternative: replace every Han-character match automatically. Rejected because it cannot distinguish diagnostics, user data, localization coverage, or frozen compatibility evidence. A blanket exemption for tests or archives would miss most of the requested migration.

### 2. Update sources before generated outputs

Translate generator templates, package docstrings, indicator catalog explanations, `api-manifest.json`, and `indicator-notes.json`; then regenerate `indicators/methods.py`, API references, indicator pages, and `_static/indicator-index.json`. Switch generated-file discovery to the new English marker while recognizing the legacy marker during this migration, so obsolete generated pages are still detected. Keep handwritten pages outside generator ownership.

Alternative: translate generated files directly. Rejected because the next generator run would restore Chinese or fail drift checks.

### 3. Preserve behavior and adapt only text dependencies

Translate project diagnostics together with their message-matching assertions. Preserve assertion counts, types, conditions, numerical values, result keys, event ordering, and serialization behavior. Update example-index categories and input-title consumers together. Translate explanatory fixture text and default demonstration labels only where doing so is part of the declared presentation change; preserve numerical arrays, digest-backed indicator outputs, serialized historical baselines, and intentional multilingual payloads.

Source edits can affect source locations and execution fingerprints. Keep existing source-line assertions meaningful and preserve execution-identity validation; do not promise that experiments tied to changed strategy source will resume with an old fingerprint. No identity check is bypassed for a translation.

Alternative: remove message assertions or regenerate all fixtures. Rejected because that would erase evidence unrelated to language.

### 4. Preserve provenance while refreshing target bytes

Translate human-readable manifest notes and record English standardization for affected target files. Refresh `targetSha256` from final bytes in both `source-manifest.json` and `extraction-manifest.json` after translation and regeneration. Preserve source revision, retrieval facts, original source hashes, source identities, mappings, and exclusions. Refresh any registered target changed by verification tooling as well.

Alternative: stop checking target hashes. Rejected because translation does not remove the package's provenance requirement.

### 5. Extend the existing static package check

Add a language-check module under `scripts/` and integrate it with `scripts/check_package.py` for repository and artifact checks. Reuse its controlled-plus-unignored file scope and build-output exclusions. Check raw text and decoded JSON/Python string content for unintended Han prose; English quality still requires human review. Unicode mathematical notation and valid multilingual input remain supported.

Store exceptions in a small JSON registry with a repository-relative path, exact value, optional semantic selector, and English rationale. Bind a test string to its intended test or field rather than exempting a whole file. Recognize exact OpenSpec rename source identifiers as protected contracts. Exclude opaque binary payloads from prose translation while continuing existing payload integrity checks. Report missing, changed, or unused exemptions; artifact checks apply only exemptions whose files are present in that artifact. Include the registry, helper, repository instructions, and OpenSpec records in the sdist so every registered exemption has its matching file and the strict check remains standalone. Extracted-source checks use the same missing-rule enforcement as repository checks.

Use focused checker tests for ordinary and escaped Chinese, narrow multilingual exemptions, stale exemptions, and artifact scope. These tests protect the new gate; translation itself uses the existing regressions. No new dependency or browser test is needed.

Alternative: an unrestricted ban on all non-ASCII characters. Rejected because it would invalidate legitimate symbols and multilingual data. A literal-only grep cannot detect escaped copy or validate exception scope.

## Risks / Trade-offs

- [Translation changes technical meaning] -> Review invariant-bearing descriptions against implementations, especially readiness, causality, sizing, and missing-data behavior.
- [English diagnostics break downstream string matching] -> Declare the message change and preserve exception types and rejection conditions; update internal assertions together.
- [Marker or link changes leave stale references] -> Support legacy marker discovery during migration, preserve anchors, and run generation and local-link checks.
- [Broad exception rules conceal regressions] -> Require exact content and an explicit purpose; reject stale rules and broad directory exclusions.
- [Hash refresh hides unrelated changes] -> Refresh only target hashes, record adaptation, and retain original source evidence and numerical baselines.
- [Archive translation appears to rewrite history] -> Translate prose and titles without changing recorded outcomes, dates, commands, task status, or past technical decisions; Git retains prior wording.

## Migration Plan

1. Retain the new root rule, reinforce it in OpenSpec configuration, and classify remaining non-English text and justified exceptions.
2. Translate source and generator inputs, then regenerate owned outputs; translate handwritten documentation, examples, tests, configuration, and OpenSpec prose. Preserve the two exact main-spec source requirement headings until the extraction-parity delta is synchronized, then translate the remaining main-spec headings. Existing scenario names remain exact matching identifiers until both the main spec and delta can be updated together without losing scenarios. Keep the delta's historical `FROM` identifiers intact.
3. Integrate the language checker and synchronize text assertions and descriptive fixtures without changing frozen computational evidence.
4. Refresh target provenance records after all final text changes. Run lint, generation checks, package integrity checks, and existing Python regressions.
5. Build wheel and sdist, check their language and resources, and record actual verification results in English. Preserve the opt-in status of slow examples.

The change needs no data migration or release automation. If implementation must be rolled back, revert its coordinated source, generated-output, assertion, checker, and target-manifest changes together; do not revert unrelated work.
