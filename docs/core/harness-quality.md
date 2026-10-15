# Harness quality evidence

Change authors maintain evidence for their checks; repository maintainers own rule exceptions and compatibility decisions. Planned capabilities are not evidence of passing tests.

| Area | Evidence entry | Verification on 2026-10-15 | Owner |
| --- | --- | --- | --- |
| Navigation | `scripts/check_harness_docs.py`, `docs/core/harness.md` | Knowledge links and strict MkDocs build passed; isolated `docs` profile passed without Node or Studio installed | Documentation maintainers |
| Verification | `scripts/verify.py`, `.verification/harness/<run-id>/result.json` | Isolated `core` passed without Node or Studio; clean full acceptance passed all 28 checks, including distribution and installation; 3,204 core tests passed with one explicitly excluded slow test | Change authors |
| Studio browser | `studio/web/e2e/`, browser check evidence | Three real journeys and three infrastructure tests passed on macOS, Python 3.12 and isolated Chromium; chart screenshot reviewed | Studio maintainers |
| Architecture | `scripts/check_architecture.py`, exact exception registry | Current graph passed; seven focused tests cover imports, re-exports, resources and exception expiry; eight reviewed adapters | Core and Studio maintainers |
| Maintenance | `scripts/doc_gardening.py`, `maintenance.json` | First scan passed with zero findings; history explicitly unknown; stable identity and failure-history tests passed | Repository maintainers |

Verified source snapshots: `10a47a02165e8edc23a935f2de4d537edb6db558` for isolated core, `3701f079739781628554fdd4e44f97e9fec98826` for isolated docs, and `b74c7f70825427d782aef5a7275ae8f3b8e0c67c` for full acceptance. These are disposable local acceptance commits based on repository commit `bad42be662df0221098a1b9e1cd8a0983fde7857`, including the proposed changes; the working repository was not committed by this task. Final documentation records the evidence after testing.

Local reports are retained under `.verification/acceptance/` and `.verification/faults/`. The full attempt is `20261015T120532Z-af531494c8`; the first maintenance attempt is `20261015T115628Z-0c2862c674`. The Chinese implementation record in `openspec/changes/archive/2026-10-15-add-repository-harness-engineering/implementation.md` records baseline repairs, commands, outcomes and remaining external verification. No trading or chart numerical expectations were refreshed; the existing drawing fixture required only its engine version identity to be corrected.

Known limits: arbitrary dynamic imports cannot be proven statically; cooperative network guards are not an OS sandbox; POSIX process behavior does not establish Windows support. GitHub Actions, the Linux matrix, Python 3.13/3.14 CI jobs and remote required-check configuration have not been verified in this local task. Historical failure rates, productivity, trends and coverage scores are unknown. The optional slow ML example was not run.

CI artifacts expire after 14 days. Preserve reviewed conclusions in a change record, and turn recurring findings into a targeted rule or regression test rather than refreshing baselines automatically. See the [harness guide](harness.md) for scope and ownership.
