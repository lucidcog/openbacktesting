## Purpose

Ensure the extracted package retains the source snapshot's implemented backtesting and research capabilities, provides an auditable migration scope and independently reproducible tests, and distinguishes identity changes from computational changes without losing functionality or weakening validation.

## ADDED Requirements

### Requirement: Auditable migration scope

Migration records MUST identify the source snapshot, imported files, and necessary external dependencies. Target file digests MUST match actual contents. Exclusions MUST have explicit reasons and MUST NOT omit required runtime modules, resources, tests, or examples. Records MUST also satisfy the zero-residual-name constraint.

#### Scenario: Verify migration manifests

- **WHEN** imported contents, target paths, and file digests are checked
- **THEN** every planned imported file is present with a matching digest, without unexplained functional removals or missing files

### Requirement: Preserve existing computational semantics

Under identical inputs, parameters, and dependencies, the new package MUST preserve the source package's public API signatures and semantics for backtests, indicators, order matching, statistics, optimization, and data-only plotting. Only predeclared package-identity, branding, and path-field changes are permitted.

#### Scenario: Regress existing numerical baselines

- **WHEN** imported fixed-market-data, strategy, order, and indicator regressions are run against the new package
- **THEN** numerical results, event order, and error boundaries satisfy existing assertions; identity and path fields follow their mappings, and numerical expectations are not rewritten for migration

### Requirement: Independent tests and examples

Imported tests and examples MUST depend only on the new package and files in the current repository, without obtaining missing functionality from the source repository or former distribution. Existing assertions MUST remain, with only identity and path adaptations. Slow examples MUST retain an explicit opt-in mechanism.

#### Scenario: Execute outside the original project layout

- **WHEN** tests and default example checks run in the repository or an independently extracted sdist
- **THEN** existing coverage executes without failures caused by missing original research records, fixtures, or parent configuration

### Requirement: Traceable validation results

Implementation delivery MUST record the actual Python version, dependency environment, static checks, regressions, and artifact validation results and identify skipped or unverified items. A proposal or successful build alone MUST NOT be presented as successful runtime acceptance.

#### Scenario: Deliver a validation record

- **WHEN** extraction implementation is declared complete
- **THEN** required checks and regressions have actual success records, and platform coverage and unexecuted optional slow examples are explicitly described
