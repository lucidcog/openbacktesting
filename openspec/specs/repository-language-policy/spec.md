# Repository Language Policy

## Purpose

Provide a consistent English default for repository development and package usage while preserving intentional multilingual content, compatibility boundaries, and reproducible generated documentation.

## Requirements

### Requirement: English repository defaults

Project-authored code, comments, docstrings, documentation, package descriptions, descriptive data fields, and default example labels MUST use English. The policy MUST cover current and archived OpenSpec documents and all controlled or non-ignored deliverable files. The repository instructions and OpenSpec project configuration MUST state this default. Established identifiers and machine-readable contracts MUST remain stable when prose is translated.

#### Scenario: Read repository and package documentation

- **WHEN** a developer reads instructions, documentation, source explanations, or package metadata
- **THEN** project-authored prose is English, including OpenSpec bodies, generated references, and default example descriptions
- **AND** API names, commands, data keys, links, and numerical definitions retain their established meaning

### Requirement: English project diagnostics

Project-authored exceptions, warnings, validation messages, CLI help, and CLI status output MUST use English. Translating these messages MUST preserve exception types, rejection conditions, exit status, and interpolation of relevant values. User-supplied or dependency-supplied text MUST retain its original content.

#### Scenario: Reject invalid input

- **WHEN** invalid input triggers an existing project validation error
- **THEN** the same failure condition raises the same exception type with an English project-authored message
- **AND** any user value included in the diagnostic is preserved without translation

### Requirement: Explicit multilingual exceptions

Non-English copy MUST be retained only when it serves an intentional multilingual or localized use case, including fixtures that exercise that use case. Exceptions MUST identify the exact retained content and its purpose; a Chinese-only default label MUST NOT qualify solely because it already exists. Language enforcement MUST NOT reject valid multilingual user input or change its runtime handling.

#### Scenario: Preserve multilingual log content

- **WHEN** a strategy supplies multilingual log text and the log is exported or serialized
- **THEN** the text round-trips unchanged
- **AND** any retained non-English fixture is explicitly identified as coverage of multilingual behavior

#### Scenario: Review a default example label

- **WHEN** an example contains a Chinese-only input title without a documented multilingual purpose
- **THEN** the default title is translated into English and related text-dependent assertions are updated

### Requirement: Reproducible English generation

Generated API descriptions, indicator reference pages, indicator search labels, and search metadata MUST use English by default. Regeneration from the committed sources MUST reproduce the committed English outputs without changing public signatures, output channels, availability, or indicator parameter contracts.

#### Scenario: Regenerate published references

- **WHEN** indicator methods and documentation are regenerated and their drift checks are run
- **THEN** generated outputs match the committed files and contain English default prose
- **AND** public signatures and indicator contracts remain unchanged

### Requirement: Static language enforcement

A repository check MUST report unintended Chinese prose with an actionable location and return a nonzero exit status. It MUST cover controlled and non-ignored deliverable text, including archived documents, and the relevant text in wheel and sdist artifacts. It MUST inspect decoded JSON strings and Python string literals as well as literal text so escaping does not bypass checks. Exceptions MUST be exact, justified, and reviewable; blanket directory exemptions MUST NOT hide project-authored prose. Unused exceptions MUST be reported. Protected identifiers and opaque historical binary payloads MUST retain their existing integrity validation.

#### Scenario: Introduce escaped Chinese default copy

- **WHEN** a developer adds unintended Chinese copy as a literal, a JSON escape, or a Python string escape
- **THEN** the check fails and identifies the file and offending text location

#### Scenario: Use an approved multilingual fixture

- **WHEN** the check encounters the exact content of a justified multilingual fixture
- **THEN** the exemption applies only to that approved content
- **AND** unrelated Chinese prose in the same file still fails the check

### Requirement: English distribution content

Distributed project-authored prose and metadata MUST follow the same English defaults as the repository. English translation MUST preserve required package resources, installation behavior, dependencies, versions, and the existing multilingual content exception.

#### Scenario: Inspect wheel and source distribution

- **WHEN** wheel and sdist artifacts are built and checked
- **THEN** their project-authored default prose and package descriptions are English
- **AND** existing resource and artifact integrity checks continue to pass
