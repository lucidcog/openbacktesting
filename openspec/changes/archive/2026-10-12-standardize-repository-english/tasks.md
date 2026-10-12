## 1. Policy and inventory

- [x] 1.1 Create root `AGENTS.md` with the English default, multilingual-copy exception, and identifier-preservation rule; verify the file exists and explicitly includes OpenSpec artifacts.
- [x] 1.2 Add the English default and exception policy to `openspec/config.yaml`; verify the configuration is accepted by `openspec status --change standardize-repository-english`.
- [x] 1.3 Classify remaining non-English text and create an exact, justified exception registry for intentional multilingual copy and associated fixtures; verify every retained Chinese string has a stated purpose and no entire source, test, documentation, or archive directory is exempted.

## 2. Source, diagnostics, and generation

- [x] 2.1 Translate comments, docstrings, and descriptive strings in non-generated `src/openbacktesting/` modules; review the diff to verify identifiers, signatures, formulas, schemas, and numerical parameters remain unchanged.
- [x] 2.2 Translate project-authored runtime errors and warnings and update their message-matching assertions together; run affected test modules and verify exception types and rejection conditions remain covered.
- [x] 2.3 Translate indicator catalog explanations, API manifest descriptions, indicator notes, and both generator templates; verify JSON parsing succeeds and catalog IDs, parameters, outputs, availability, and API signatures are unchanged.
- [x] 2.4 Migrate generated-file marker discovery, regenerate indicator methods and documentation, and verify `uv run --locked python scripts/generate_indicator_api.py --check` and `uv run --locked python scripts/core_docs.py --check` pass without stale generated pages.

## 3. Documentation, examples, and tests

- [x] 3.1 Translate `README.md`, handwritten `docs/core/` pages, example documentation, and fixture documentation; review terminology and verify local paths, links, explicit anchors, commands, and numerical examples retain their meaning.
- [x] 3.2 Translate default example labels and descriptive payload text, and synchronize example-index parsers, input-title consumers, and text-dependent fixture expectations; run `tests/test_examples.py` and verify execution coverage and numerical expectations remain intact.
- [x] 3.3 Translate test and probe comments, docstrings, assertion explanations, skip reasons, and descriptive fixture notes; run affected tests and verify frozen numerical hashes and historical pickle payloads have not been regenerated.
- [x] 3.4 Preserve and register purposeful multilingual log, input, serialization, and localized-copy fixtures; run the relevant existing tests and verify exact Unicode round-trips remain covered.
- [x] 3.5 Translate project metadata, configuration prose, and maintenance-script messages; verify `pyproject.toml` parses and package name, version, dependencies, and configuration behavior remain unchanged.
- [x] 3.6 Synchronize the extraction-parity delta through the standard OpenSpec spec-sync workflow, then translate remaining current and archived OpenSpec prose and headings; coordinate any scenario-name translation between the main spec and delta and verify `openspec validate standardize-repository-english --strict` passes without lost scenarios, historical `FROM` identifiers remain intact, and recorded facts and task status are preserved.

## 4. Static language checks

- [x] 4.1 Implement the language-check helper and integrate it with `scripts/check_package.py` using the existing repository and artifact file scopes; verify failures identify unintended Chinese text in raw content, decoded JSON, and Python string literals.
- [x] 4.2 Implement exact exception matching, protected-identifier handling, and unused-rule reporting; verify a retained multilingual fixture passes while unrelated Chinese prose in the same file fails.
- [x] 4.3 Add focused tests for escaped strings, stale exceptions, repository scope, and wheel/sdist scope; run the new checker tests and verify they exercise successful and failing checks without altering existing integrity rules.
- [x] 4.4 Include the checker helper, registry, repository instructions, and OpenSpec records in the sdist and document the check in the English development guide; verify the checker works from an independently extracted source distribution.

## 5. Provenance

- [x] 5.1 Translate human-readable notes in both provenance manifests and record language-only adaptations for affected registered targets; verify original source revisions, source digests, mappings, counts, and exclusion facts remain unchanged.
- [x] 5.2 Refresh target digests from final translated and regenerated file bytes; verify `uv run --locked python scripts/check_package.py` passes with no missing targets, digest mismatches, invalid links, or unintended Chinese prose.

## 6. Integrated verification and delivery

- [x] 6.1 Run `uv run --locked ruff check src tests examples scripts conftest.py` and both generator drift checks; verify all commands pass after the final edits.
- [x] 6.2 Run `uv run --locked python -m pytest` and `uv run --locked python -m openbacktesting.test`; verify existing numerical, behavioral, serialization, multiprocessing, and multilingual assertions pass, and explicitly record optional slow-example skips.
- [x] 6.3 Build with `uv build --no-sources` and run `uv run --locked python scripts/check_package.py --artifact dist/openbacktesting-0.2.0-py3-none-any.whl --artifact dist/openbacktesting-0.2.0.tar.gz`; verify English defaults, resources, metadata, and source-distribution checker availability.
- [x] 6.4 Record actual validation commands and results in an English implementation record and document the diagnostic-message compatibility change; verify remaining Han matches are only approved multilingual content or protected migration identifiers, and do not claim unexecuted checks passed.
