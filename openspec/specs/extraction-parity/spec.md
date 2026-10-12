# extraction-parity Specification

## Purpose

Ensure the extracted package retains the source snapshot's implemented backtesting and research capabilities, provides an auditable migration scope and independently reproducible tests, and distinguishes identity changes from computational changes without losing functionality or weakening validation.

## Requirements

### Requirement: Auditable migration scope

Migration records MUST identify the source snapshot, imported files, and necessary external dependencies. Target file digests MUST match actual contents. Exclusions MUST have explicit reasons and MUST NOT omit required runtime modules, resources, tests, or examples. Records MUST also satisfy the zero-residual-name constraint.

#### Scenario: Verify migration manifests

- **WHEN** imported contents, target paths, and file digests are checked
- **THEN** every planned imported file is present with a matching digest, without unexplained functional removals or missing files

### Requirement: Preserve existing computational semantics

Under identical inputs, parameters, and dependencies, the package MUST preserve the source snapshot's public API signatures and the semantics of backtests, indicators, order matching, statistics, optimization, and data-only plotting. Declared differences MUST be limited to package identity, brand identifiers, paths, and English translations of project-authored presentation text and diagnostics. Translation MUST preserve exception types, failure conditions, numerical definitions, event order, and serialized field contracts. User-supplied multilingual text MUST NOT be translated.

#### Scenario: Regress existing numerical baselines

- **WHEN** fixed-market-data, strategy, order, and indicator regressions are run against the package
- **THEN** numerical results, event order, and error boundaries satisfy the existing assertions
- **AND** only identity fields, paths, and declared project-authored text change; numerical expectations are not rewritten to accommodate translation

#### Scenario: Trace translated file content

- **WHEN** translation changes a file recorded in a provenance manifest
- **THEN** its target digest matches the translated bytes and the language-only adaptation is recorded
- **AND** original source revisions, source digests, mappings, and numerical baseline evidence remain intact

### Requirement: Independent tests and examples

Tests and examples MUST depend only on the package and files in the current repository, without obtaining missing behavior from a source repository or former distribution. Existing assertions MUST remain in place; only identity fields, paths, and text-dependent expectations affected by the declared English migration are permitted adaptations. Intentional multilingual fixtures MUST retain their coverage. Slow examples MUST keep their explicit opt-in mechanism.

#### Scenario: Execute outside the original project layout

- **WHEN** tests and default example checks run in the repository or an independently extracted sdist
- **THEN** their existing coverage executes without missing research records, fixtures, or parent configuration
- **AND** English presentation changes do not weaken numerical, behavioral, or multilingual assertions

### Requirement: Traceable validation results

Implementation delivery MUST record the actual Python version, dependency environment, static checks, regressions, and artifact validation results and identify skipped or unverified items. A proposal or successful build alone MUST NOT be presented as successful runtime acceptance.

#### Scenario: Deliver a validation record

- **WHEN** extraction implementation is declared complete
- **THEN** required checks and regressions have actual success records, and platform coverage and unexecuted optional slow examples are explicitly described
