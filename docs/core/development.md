# Local development and validation

Public behavior changes require corresponding updates to guides, API references, runnable examples, and validation. Runtime source lives under `src/openbacktesting/`, divided into data, broker, strategy, simulation, portfolio, optimizer, and indicators; the package exports its public entry points.

## Repository layout and prerequisites

Use Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Python **3.12–3.14**. Core and documentation work do not require Node.js. Studio frontend development additionally needs **Node.js 22.12+** and npm. Studio has been exercised on macOS; its POSIX filesystem protections have not been verified on Windows.

| Area | Source and checks |
| --- | --- |
| Python framework | `src/openbacktesting/`, `tests/`, root `pyproject.toml` and `uv.lock` |
| Studio Python host | `studio/src/openbacktesting_studio/`, `studio/tests/` |
| Studio interface | `studio/web/src/`, `studio/web/package-lock.json` |
| Vendored charts | `studio/vendor/lightweight-charts/`, `studio/vendor-metadata/` |
| Documentation and examples | `docs/core/`, `scripts/docs/`, `examples/` |
| Planning and archived decisions | `openspec/` |

For a new checkout, clone the repository (or [your fork](contributing.md#fork-and-make-a-focused-branch)) and enter its root:

```sh
git clone https://github.com/lucidcog/openbacktesting.git
cd openbacktesting
uv sync --locked --extra test --group docs
uv run --locked python examples/advanced/native_run.py
```

`uv sync` creates `.venv` and installs the core project for development. The example uses bundled data. Work on the source under `src/`; you do not need to rebuild a wheel for each Python edit. All commands below run from the repository root unless stated otherwise.

## Core development

Start with the test module relevant to your change, for example:

```sh
uv run --locked python -m pytest tests/test_inputs.py -q
```

Use Ruff on the Python files you changed, with the configuration in `pyproject.toml`; avoid formatting unrelated files. Before submitting core behavior changes, run the broader checks below.

### Core validation and distribution

Run from the current repository root:

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
uv run --locked python scripts/generate_indicator_api.py --check
uv run --locked python scripts/core_docs.py --check
uv build --no-sources
uv run --locked python scripts/check_package.py --artifact dist/openbacktesting-0.2.1-py3-none-any.whl --artifact dist/openbacktesting-0.2.1.tar.gz
```

`uv.lock` fixes this repository's validation environment and is distributed with the sdist. Independent installations resolve dependencies from `pyproject.toml` and do not require the lockfile. After extracting the sdist, establish the environment with `uv sync --locked --extra test`, then run the same Python test commands. Historical baselines compare dependency-version fields exactly, so full regression requires the locked environment; identity differences from other dependency versions must not be treated as numerical regressions. Enable the complete slow ML examples explicitly with `OPENBACKTESTING_RUN_SLOW_EXAMPLES=1`; they do not run by default.

In addition to SAMBO, the `optimize` extra declares scikit-learn, which brings in joblib. The current SAMBO top-level import requires these dependencies; a base backtesting installation does not add them.

## Studio development

The core and Studio are separate distributions in one repository. Build the web assets **before** installing the editable Studio package; its build hook validates the asset manifest.

```sh
npm --prefix studio/web ci --ignore-scripts
npm --prefix studio/web run build
uv venv --python 3.12 studio/.venv
uv pip install --python studio/.venv/bin/python -e . -e 'studio[test]'
studio/.venv/bin/python -m openbacktesting_studio.cli examples/strategies --no-open
```

Open the complete terminal URL, including the one-time token, in your browser. Select a workspace directory and use the [Studio walkthrough](studio/index.md) to run a sample strategy. The default port is 8765; use a different fixed `--port` when occupied. Ctrl+C stops the host. The commands above use a dedicated environment, so a later root `uv sync` cannot remove Studio's dependencies from it.

Both packages are editable in this environment: changes to core or Studio Python code are read from the checkout. This command resolves the declared dependency ranges; it is not a replay of the root lockfile. Use the root locked environment for core baseline comparisons. The separate Studio lockfile uses the local core checkout through `[tool.uv.sources]`; after building web assets, `uv sync --project studio --locked --extra test` installs both editable packages. This source override is for repository development only; wheel metadata retains the core version requirement. Install both built distributions together when testing an unpublished core release.

### Edit, rebuild, and inspect

For a frontend change, edit `studio/web/src/`, run the relevant tests and type checks, rebuild, and reload the Studio page. Restart the Python host after host or protocol changes. Reloading the browser alone does not reload Python modules in the running host.

```sh
npm --prefix studio/web run typecheck
npm --prefix studio/web run lint
npm --prefix studio/web test
npm --prefix studio/web run build
studio/.venv/bin/python -m pytest studio/tests -q
```

`npm --prefix studio/web run dev` starts Vite, but the current Vite configuration has **no API proxy or integrated session setup**. It is not the complete Studio development server. Use the built interface served by the Python host for end-to-end browser checks; do not disable origin or session checks to make a separate frontend origin work.

The interface uses React, TypeScript, shadcn/ui, and the vendored Lightweight Charts source. Use existing components and styling conventions. Preserve upstream licenses and record chart source modifications in `studio/vendor-metadata/lightweight-charts.json`; `studio/scripts/check_vendor.py` verifies the recorded file identities. Never replace the vendored tree with an untracked local or CDN build.

After changing Studio protocol models, regenerate their checked-in schemas with `studio/.venv/bin/python studio/scripts/export_schemas.py` and review the diff. Build both packages and run installation checks when changing distribution behavior:

```sh
uv build --out-dir dist
uv build studio --out-dir studio/dist
studio/.venv/bin/python studio/scripts/check_distribution.py studio/dist/*.whl studio/dist/*.tar.gz
studio/.venv/bin/python studio/scripts/check_installation.py --python 3.12
```

The installation check creates isolated environments, exercises the core and Studio artifacts outside the checkout, and checks local assets and offline runtime behavior. Frontend component tests and HTTP worker tests do not replace a browser check of charts, file editing, navigation, and the workflow affected by a UI change.

## Choose checks for your change

| Change | Validation to run |
| --- | --- |
| Core behavior | Relevant regression tests, then the core validation commands above; update affected examples and references |
| Studio host or execution | Relevant `studio/tests` modules; broader Studio tests and an actual run when execution changes |
| Studio interface | Relevant component tests, typecheck, lint, build, and the affected workflow in a browser |
| Documentation prose or links | `uv run --locked --group docs mkdocs build --strict`; inspect the changed pages |
| Documentation generation or site tooling | Generation drift checks and the documentation tests described below |
| Package contents or dependencies | Build artifacts, distribution integrity, and clean installation checks |
| Vendored chart source | Vendor identity verification, relevant upstream tests, and actual chart rendering |

Run `uv run --locked python scripts/check_language.py` and `git diff --check` for authored changes. Record commands and outcomes in the PR, including any pre-existing failure or check you could not run. Do not change baselines, manifests, or exclusions merely to hide a failure. The [contribution guide](contributing.md) covers reporting, review, and sharing reproducible examples.

## Documentation and generated interfaces

The manual is readable as Markdown or as a MkDocs Material site. The public API inventory is `api-manifest.json`. User-facing reference introductions live in `scripts/docs/*.md.in`; `scripts/user_docs.py` combines them with current callable signatures and attribute summaries. Indicator purposes are in `indicator-notes.json`; parameter meanings are in `indicator-parameters.json`. After changing interfaces or the catalog, regenerate and check:

```sh
uv run --locked python scripts/generate_indicator_api.py
uv run --locked python scripts/core_docs.py
uv run --locked python scripts/check_package.py
```

`generate_indicator_api.py` generates indicator methods from the fixed catalog. `core_docs.py` generates references from the reviewed templates and installed objects, keeping private constructors and maintenance inventories out of the user path. Edit templates rather than generated reference pages. Guides and the quickstart are handwritten. Run `uv run --locked python -m pytest tests/test_user_documentation.py tests/test_examples.py` to execute the complete manual examples, every available indicator-page example, and the repository tutorials; navigation checks also validate local anchors. Review prose against implementation before regenerating. The [maintainer API inventory](reference/classification.md) retains compatibility/internal classifications separately from the user navigation.

### Preview and build the documentation site

```sh
uv run --locked --group docs mkdocs serve
uv run --locked --group docs mkdocs build --strict
```

The preview runs at `http://127.0.0.1:8000` with live reload; the static build is written to `build/docs/`. Use `--dev-addr 127.0.0.1:8001` if the default port is occupied. The `docs` dependency group is locked separately from runtime dependencies. The site needs no JavaScript toolchain, external search service, or remote fonts.

For an isolated build suitable for hosting, run `bash scripts/build_docs.sh`. It installs only documentation dependencies into `build/docs-env/`. The [Cloudflare Pages deployment guide](deployment.md) lists the exact build command, output directory, and environment settings.

`mkdocs.yml` defines the navigation, theme, and browser-side search. `scripts/docs_site.py` groups indicator pages from the generated index and includes linked repository examples as highlighted source pages. It rewrites links only during the build, so the same Markdown remains readable in the repository. All manual pages participate in search; use names such as `Backtest`, `OrderRequest`, or `ta.ema`. The strict build rejects missing navigation targets, broken local links, and broken anchors. Building or serving the site renders the current Markdown; regenerate API references separately after source or template changes using the commands above.

`scripts/docs_discovery.py` derives page titles and summaries from the visible content unless front matter explicitly supplies them. It generates portable Markdown, LLM indexes, canonical metadata, structured data, sitemap filtering, and crawler headers. Keep the full introductory heading descriptive even when a sidebar label is abbreviated. The publication and preview policies are documented in the [deployment guide](deployment.md#search-visibility).

Run `uv run --locked --group docs --extra test python -m pytest tests/test_docs_discovery.py` after changing the site pipeline. This builds production and preview sites, checks every HTML/Markdown counterpart, verifies all published Markdown links and source code fences, and confirms sitemap coverage, unique metadata, structured data, and preview indexing controls. When Node.js is available, `node --test tests/test_page_tools.cjs` checks exact clipboard contents, unavailable/denied clipboard access, failed downloads, retry, and repeated clicks without npm dependencies. Node.js is not required to build or serve the documentation. Also check the copy button in the browser with keyboard access, both color schemes, and narrow viewports.

## Distribution integrity

The wheel includes runtime source, `py.typed`, indicator and Portfolio catalogs, result schemas, and built-in CSV data. The sdist additionally includes tests, fixtures, examples, the manual, provenance manifests, and local checking tools. In an independent environment, verify from a working directory without source that the loaded package belongs to site-packages, and exercise a minimal backtest, resource access, pickle, spawn, and optimization-result saving and recovery.

`check_package.py` scans project paths and content with case-insensitive naming rules, covering documentation, tests, OpenSpec, and artifact metadata. It also checks file manifests, Python syntax, documentation links, and unintended Chinese prose, including decoded JSON and Python strings. Exact multilingual exceptions require an English rationale; missing, changed, or unused exceptions fail validation. The same language checks apply to wheel and sdist content. Deliverable files must not be excluded to hide matches.

## Provenance and behavioral boundaries

The [historical source manifest](../../source-manifest.json) preserves earlier upstream evidence; the [extraction manifest](../../extraction-manifest.json) records the direct source snapshot and path mappings. Source paths are normalized to the new identity, source digests still identify original bytes, and target digests identify current content.

The extraction migration preserves API signatures, computed values, and event order while adapting identity and paths. The declared English standardization additionally translates project-authored presentation text and diagnostics; consumers matching former Chinese messages must update, while exception types and rejection conditions remain unchanged. Pickles referencing old module paths do not load automatically; old-brand semantic archives are not guaranteed to be directly readable, and old experiments cannot resume under a new execution identity. Data with the new identity supports normal saving, reading, and recovery. See [current limitations](limitations.md) for usage boundaries.

New capabilities must extend the example index and actual execution validation; syntax checks alone are insufficient for delivery. Internal refactoring must demonstrate unchanged public behavior. The core framework does not depend on desktop components, a parent workspace, or a JavaScript toolchain. Studio requires a JavaScript toolchain only when building its frontend from source.

The source distribution includes repository instructions and OpenSpec records so the language exception registry has the same complete file scope when checked after extraction. Running the Python integrity checker does not require the OpenSpec CLI.
