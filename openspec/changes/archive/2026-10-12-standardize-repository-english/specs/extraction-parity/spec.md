## RENAMED Requirements

- FROM: `### Requirement: 保持既有计算语义`
- TO: `### Requirement: Preserve existing computational semantics`
- FROM: `### Requirement: 测试和示例独立运行`
- TO: `### Requirement: Independent tests and examples`

## MODIFIED Requirements

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
