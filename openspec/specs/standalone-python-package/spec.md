# standalone-python-package Specification

## Purpose

Ensure users can install, run, and develop the standalone backtesting package using only this repository or its distribution artifacts, with complete runtime resources, examples, and necessary materials, while leaving the source repository and its working state unchanged throughout extraction.

## Requirements

### Requirement: Independent build and installation

The project MUST build wheel and sdist distributions named `openbacktesting` from the repository root on supported Python versions. Building, installing, and running MUST NOT depend on the source repository, a parent workspace, desktop modules, or JavaScript tooling. The initial version MUST be `0.2.0`, supporting Python `>=3.12,<3.15`.

#### Scenario: Install both artifacts independently

- **WHEN** wheel and sdist artifacts are installed separately in environments without the former package or access to the source repository
- **THEN** both install successfully, `import openbacktesting` works, distribution version matches `openbacktesting.__version__`, and a minimal backtest completes

### Requirement: Complete runtime resources and optional dependencies

The wheel MUST carry all required runtime resources, including type markers, indicator and statistics catalogs, result schemas, and bundled sample data. Base installation MUST support backtests without optional optimizers. The `optimize` and `test` extras MUST retain their corresponding capability boundaries.

#### Scenario: Read resources from an installed environment

- **WHEN** a user leaves the source directory, reads resources through the installed package, and runs a bundled-data example
- **THEN** resource access and the backtest succeed without accessing the source workspace

#### Scenario: Respect optional optimizer boundaries

- **WHEN** an optimization method is called without its optional optimizer in a base installation
- **THEN** it reports a clear missing-dependency error, and installing the `optimize` extra enables the corresponding minimal optimization flow

### Requirement: Complete local development materials

The project and sdist MUST provide local fixtures, configuration, documentation, and data needed for existing tests and examples. Instructions MUST supply valid standalone installation, minimal-backtest, test, and build commands. Internal links MUST NOT point into the original project layout.

#### Scenario: Develop from the source distribution

- **WHEN** a developer extracts the sdist and installs test dependencies
- **THEN** bundled instructions can run tests and examples, all required files exist in the extraction directory, and the absent original repository causes no file-resolution failures

### Requirement: Read-only source repository

This extraction MUST write files and run file-producing operations only inside the current repository. It MUST NOT modify source repository code, configuration, Git state, caches, or build output.

#### Scenario: Verify source state after extraction

- **WHEN** source digests and working-tree state are compared before and after extraction
- **THEN** this operation has caused no changes; external concurrent changes are reported accurately and are not reverted
