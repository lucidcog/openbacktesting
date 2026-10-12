## Purpose

Establish a unique and consistent distribution, import, and data identity for the standalone backtesting package, preventing residual names from directing users to former entry points and defining compatibility boundaries for serialization, execution-environment identities, and persisted data.

## ADDED Requirements

### Requirement: Unique public identity

Distribution metadata, the import root, and public object module ownership MUST use `openbacktesting`. The display name MUST be `OpenBacktesting`, and dedicated environment variables MUST use the `OPENBACKTESTING_` prefix. The package MUST NOT provide former-package aliases, forwarding modules, or fallback to old environment variables.

#### Scenario: Inspect installed package identity

- **WHEN** a user queries distribution metadata, imports public objects, and inspects module paths
- **THEN** the package and objects use the new identity, and artifacts contain no former package root or compatibility entry points

### Requirement: Deliverables contain no former names

Paths and contents of controlled repository files, non-ignored files awaiting inclusion, wheel artifacts, and sdist artifacts MUST contain neither user-prohibited former project names nor former package names. Matching MUST ignore case. Documentation, OpenSpec, test data, manifests, metadata, and check rules MUST obey the same constraint.

#### Scenario: Check names across the entire scope

- **WHEN** project deliverables and distribution artifacts undergo name checks
- **THEN** no prohibited name matches occur; documentation exemptions or deletion of in-scope files cannot conceal residual names

### Requirement: Consistent data and execution identity

New output, catalogs, and schemas MUST consistently use `openbacktesting_portfolio_v1` as the Portfolio semantic identity and `openbacktesting.numpy` as the local indicator backend identity. Experiment environments MUST record the new distribution identity. Identity changes MUST NOT alter unrelated numerical definitions or field contracts.

#### Scenario: Persist and restore new data

- **WHEN** a user generates Portfolio results and optimization experiments, saves and reopens them, and resumes eligible new experiments under the existing contract
- **THEN** results pass the new schema, execution identities agree, and statistical values and experiment state restore correctly

### Requirement: Explicit serialization and historical compatibility boundaries

New-identity objects MUST support existing serializable objects' pickle round-trips and multiprocessing transfer. The project MUST state that old-module-path pickles are not migrated automatically, former branded-protocol archives are not guaranteed to load directly, and old experiments cannot resume under the new identity. Mismatched execution identities MUST NOT silently be treated as resumable.

#### Scenario: Use new-identity objects across processes

- **WHEN** public serializable objects undergo pickle round-trips and spawn transfer
- **THEN** objects restore correctly with module paths under the new import root

#### Scenario: Resume with a mismatched execution identity

- **WHEN** a user attempts to restore an existing experiment under a different execution identity
- **THEN** identity validation rejects resumption and preserves the existing experiment data
