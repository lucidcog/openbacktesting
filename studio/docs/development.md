# Building and validating Studio

For the shared contributor workflow, see [local development](https://docs.openbacktesting.com/development/#studio-development) and the [contribution guide](https://docs.openbacktesting.com/contributing/).

The lightweight monorepo keeps core code under root `src/openbacktesting/` and the
optional application under `studio/`. Neither package imports the other's implementation
in reverse: Studio depends on public core APIs; core never depends on Studio.

From the repository root, use Node 22.12+ only for development:

```sh
npm --prefix studio/web ci --ignore-scripts
npm --prefix studio/web run typecheck
npm --prefix studio/web run lint
npm --prefix studio/web test
npm --prefix studio/web run build
uv build studio --out-dir studio/dist
python studio/scripts/check_distribution.py studio/dist/*.whl studio/dist/*.tar.gz
```

`build` verifies the complete vendored chart source identity, installs its locked
build tools with hooks disabled, builds that local source, then bundles the application.
Monaco and its worker resolve locally, not through the loader's CDN default. The editor
is a separate lazy chunk. All emitted resources and frontend input hashes are recorded
in `build-manifest.json`. The Python build hook rejects missing, mutated or stale assets.
The sdist carries these verified resources so consumers do not run Node.

Set up the Python development environment with `uv venv studio/.venv`, then
`uv pip install --python studio/.venv/bin/python -e . -e 'studio[test]'`.
Launch with `studio/.venv/bin/python -m openbacktesting_studio.cli examples/strategies --no-open` and open the complete printed URL. Rebuild after frontend changes and reload the page; restart the host after Python host changes. Vite currently has no API proxy or integrated session setup, so `npm run dev` alone is not a complete Studio server.

Run `studio/.venv/bin/python -m pytest studio/tests`, and preserve the existing core
regression/integrity/language checks when changing shared scripts. The editable install resolves declared dependency ranges. The separate Studio lockfile selects the local core checkout through `[tool.uv.sources]`; after building web assets, `uv sync --project studio --locked --extra test` installs both editable packages. Built distributions retain `openbacktesting>=0.2.1,<0.3` as their dependency, without a local path. Use the root locked environment for core baseline comparisons.

The UI uses React/TypeScript, shadcn/ui (Radix), compact TradingView-inspired tokens,
IBM Plex Sans/Mono, and the local Lightweight Charts build. Chart projection, form parsing,
editor conflicts, workflow ordering and synchronization are tested without a browser.
The backend tests exercise real short worker processes and HTTP contracts. These checks
are not browser E2E, screenshot validation or an accessibility audit; none is claimed.

See [the provenance guide](../vendor-metadata/README.md) before changing or upgrading
chart source. Upstream tests are retained. Source maps, frontend source and Node runtime
are not needed by end users. Keep generated web assets out of Git while including them
in distributions through the explicit Hatch artifact rule.
