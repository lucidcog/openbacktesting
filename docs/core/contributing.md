---
title: Contributing code, examples, and documentation
description: Report issues, develop a focused change, share reproducible strategies, and submit a pull request to OpenBacktesting.
---

# Contributing to OpenBacktesting

Contributions can improve the Python framework, Studio, examples, tests, documentation, or translations. You do not need to work on every part of the repository. Start with a focused problem and use the [local development guide](development.md) for the environment and checks relevant to your change.

## Find or describe the problem

Search [existing issues](https://github.com/lucidcog/openbacktesting/issues) and [pull requests](https://github.com/lucidcog/openbacktesting/pulls) before starting. A small bug fix or documentation correction can go directly to a PR. Discuss a substantial feature, dependency, public API change, or execution-semantics change in an issue first so its scope and compatibility tradeoffs can be reviewed.

For a bug report, include:

- Python, OpenBacktesting, and dependency versions; for Studio, include its version, browser, and operating system.
- A minimal script or sequence of UI actions, plus small synthetic or redistributable input data.
- Expected and actual behavior, the traceback or relevant logs, and the command that reproduces it.
- For a numerical or execution discrepancy, the affected bars, settings, and observations that establish the difference.

For a feature request, explain the user problem and the behavior you want, including a concrete example and relevant constraints. A screenshot helps with a UI issue, but a reproducible sequence makes it actionable. Remove credentials, account identifiers, private paths, and proprietary data from public reports.

## Fork and make a focused branch

Fork `lucidcog/openbacktesting` on GitHub if you do not have write access. Clone your fork and add the upstream repository. Replace `YOUR-USERNAME` with your own GitHub username:

```sh
git clone https://github.com/YOUR-USERNAME/openbacktesting.git
cd openbacktesting
git remote add upstream https://github.com/lucidcog/openbacktesting.git
git fetch upstream
git switch -c fix-descriptive-name upstream/main
```

This creates the contribution branch from current upstream `main`. Use a descriptive branch name for your change. If you already have a checkout, save or commit your current work before switching; do not reset unrelated changes. Follow [local development](development.md) to install the required tools and dependencies.

Keep one logical change in a PR. Separate unrelated refactors, formatting sweeps, dependency upgrades, and generated-file updates from a behavior fix. A draft PR can be useful when you want feedback before the implementation is complete.

## Implement and validate

- Preserve public contracts unless the change intentionally revises them. Explain changes to execution timing, indicator values, report schemas, or persisted experiment compatibility.
- Add a meaningful regression test for a behavioral bug, ideally showing that it fails before the fix and passes afterward. Test the observable result, not a copy of the implementation. Documentation-only corrections usually need link and build checks rather than new unit tests.
- Update the guide, API reference source, or runnable example that teaches changed behavior. Edit templates for generated documentation and regenerate the output; do not hand-edit generated pages alone.
- Keep core independent of Studio. Use public core APIs in Studio, existing shadcn/ui components for its controls, and the recorded vendor workflow for chart-library modifications.
- Use English for code, comments, product text, and general documentation. OpenSpec planning and implementation records use Simplified Chinese, while structural keywords and identifiers keep their spelling. Follow the exact-path language registry and preserve intentional localized fixtures and third-party originals.

See the [check selection table](development.md#choose-checks-for-your-change) for focused and broader validation. Report commands, outcomes, and any unverified behavior accurately. If a check already fails on the base revision, include that evidence; do not silently remove a test, loosen an assertion, or change a numerical baseline to make it pass.

Larger changes may use the repository's existing OpenSpec workflow to capture requirements and design. Coordinate that scope with maintainers; a typo fix does not need a new specification. Read [AGENTS.md](../../AGENTS.md) before using coding agents and review their output as you would any other contribution.

## Share a strategy, example, or result

A useful shared example should run independently and explain what it demonstrates:

1. Include the strategy source, required dependencies, exact run command, and parameter values.
2. Prefer bundled sample data or a small synthetic dataset. If external data is essential, document how to obtain it and its license instead of committing a private dataset.
3. State the timeframe, timezone, instrument assumptions, fees, and other execution settings needed to interpret the result.
4. Describe the expected behavior. When contributing an example to the repository, update the example index and add appropriate execution validation.

Studio's **Export result** produces a `.obstudio` archive. Include source, normalized data, or logs only when needed and when you can share them; those resources are optional. A screenshot alone cannot reproduce the result, and a saved result without source is not a runnable strategy. See [Studio sharing and reopening](studio/index.md#save-share-and-reopen) for the user workflow. Attach a suitable small artifact to the issue or PR when useful, rather than committing an entire workspace's `.openbacktesting/` history.

Do not include `.env`, tokens, private market data, virtual environments, `node_modules`, build outputs, or local run databases in a PR. Inspect the staged diff and filenames before committing. Keep existing license notices and record the origin and license of any newly introduced third-party material. Contributions are submitted under the project's [Apache-2.0 license](../../LICENSE); preserve the separate terms of vendored components.

## Open a pull request

Review and commit only the intended files. The paths below are placeholders for your changes:

```sh
git status --short
git diff
git add path/to/changed-file path/to/regression-test
git diff --cached
git commit -m "Explain the concrete change"
git push -u origin fix-descriptive-name
```

On GitHub, open a pull request with **base repository `lucidcog/openbacktesting`, base branch `main`**, and your fork's contribution branch as the head. Use your own contributor account. Check the changed-files view to make sure the PR contains the intended scope.

A useful PR description includes:

- **Problem:** what failed or was missing, with an issue link where applicable.
- **Change:** the resulting behavior and any compatibility or design tradeoffs.
- **Validation:** the exact checks you ran, their results, and any known failures or untested platforms.
- **UI evidence:** before/after screenshots or a short recording for visible changes, with the reproduction steps.

Use `Fixes #123` only when the PR resolves that issue. Do not claim unrun tests passed or assume that automated checks cover manual browser behavior. A draft should make unfinished work explicit.

## Respond to review

Keep discussion specific and respectful. Explain the behavior or evidence behind a choice, and ask when feedback is unclear. Address review comments with follow-up commits on the same branch; pushing to that branch updates the PR. Rerun checks affected by your revisions and update the description when the final scope changes.

If the branch needs newer upstream changes, fetch and merge upstream `main`, resolve conflicts, and rerun the affected checks. Avoid rewriting a shared branch's history without coordinating with the people using it. Maintainers decide when the change is ready to merge; opening a PR does not promise acceptance or a response deadline.

## Further reading

The structure follows common open-source contribution practices: [GitHub's contributor-guidelines documentation](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors) explains the repository entry point, and [NumPy's contribution guide](https://numpy.org/doc/stable/dev/index.html) illustrates the fork, test, PR, and review cycle. OpenBacktesting's commands and project-specific requirements are documented here and in [local development](development.md).
