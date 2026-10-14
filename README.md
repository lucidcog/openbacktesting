# OpenBacktesting

**Historical backtesting in Python, from strategy rules to inspectable results.**

**English** · [简体中文](docs/readme/README.zh-CN.md) · [Español](docs/readme/README.es.md) · [Português (Brasil)](docs/readme/README.pt-BR.md) · [Français](docs/readme/README.fr.md) · [Deutsch](docs/readme/README.de.md) · [Italiano](docs/readme/README.it.md) · [हिन्दी](docs/readme/README.hi.md)

Write bar-by-bar strategies, evaluate them on historical market data, and inspect orders, trades, equity, and risk statistics. OpenBacktesting is a standalone Python package with indicators, parameter optimization, Portfolio reports, and plotting-data export.

**Python 3.12–3.14** · **Version 0.2.0** · Distribution and import: `openbacktesting`

[Quick start](#quick-start) · [Manual](https://docs.openbacktesting.com/) · [Examples](https://docs.openbacktesting.com/examples/) · [Local development](#local-development) · [Contribute](CONTRIBUTING.md) · [Report an issue](https://github.com/lucidcog/openbacktesting/issues)

## Top sponsor — Pineify

<a href="https://pineify.app">
  <img src="docs/assets/pineify-logo.svg" alt="Pineify" width="96">
</a>

**[Pineify](https://pineify.app) is OpenBacktesting's top paid sponsor.** Its financial support helps fund this project.

Pineify is an AI trading toolkit for building indicators and strategies across multiple platforms. It brings together Pine Script AI, a Finance Agent, AI stock picking, market screening, chart analysis, and MCP tools. [Explore Pineify →](https://pineify.app)

## What you can do

- **Build strategies:** use a bar-by-bar lifecycle, typed inputs, built-in indicators, and composable helpers.
- **Inspect execution:** examine orders, fills, position sizing, fees, closed trades, and open lots.
- **Analyze results:** read pandas statistics, equity curves, and immutable Portfolio reports for each run.
- **Compare parameters:** run grid searches or optional SAMBO optimization, save experiment results, and export plotting data for your own renderer.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and use Python `>=3.12,<3.15`. From a terminal:

```sh
git clone https://github.com/lucidcog/openbacktesting.git
cd openbacktesting
uv sync --locked
uv run --locked python examples/advanced/native_run.py
```

The example uses bundled GOOG historical data; no market-data download is required. It prints return, trade count, maximum drawdown, and result tables. See [your first backtest](https://docs.openbacktesting.com/quickstart/) for a walkthrough.

To install the checked-out source into an existing Python environment instead:

```sh
python -m pip install .
```

The base dependencies are NumPy, pandas, and `pandas-ta-classic==0.8.32`. For SAMBO optimization, use `python -m pip install '.[optimize]'` or `uv sync --locked --extra optimize`. These are source-installation instructions; they do not assume a PyPI release. [Build and distribution details](https://docs.openbacktesting.com/development/).

## Optional Studio

Use [OpenBacktesting Studio](docs/core/studio/index.md) to edit local strategy files, configure inputs, inspect charts and reports, and compare parameter experiments in your browser. It is a separate Python distribution; framework-only users do not install its web assets. The illustrated guide covers building and installing the current source version, launching Studio, and running your first strategy.

## Minimal backtest

Save this as `quickstart.py` in the repository root and run `uv run --locked python quickstart.py`:

```python
from openbacktesting import Backtest, Strategy
from openbacktesting.test import GOOG


class BuyAndHold(Strategy):
    def init(self):
        pass

    def next(self):
        if self.bar_index == 0:
            self.buy(qty=1)


result = Backtest(GOOG, BuyAndHold, end_policy="close_at_last_close").run()
print(result[["Return [%]", "# Trades", "Max. Drawdown [%]"]])
```

This strategy requests one unit on the first bar. Default execution occurs at the next bar's open; `close_at_last_close` closes the remaining position at the final close.

`run()` returns a pandas Series. Use `result["_trades"]` for trades and `result["_equity_curve"]` for equity history. See the [results guide](https://docs.openbacktesting.com/guides/results/) for the full field list and Portfolio export; underscore-prefixed fields are native diagnostics, not a stable cross-language contract.

## Documentation

[Manual](https://docs.openbacktesting.com/)

The detailed manual and examples are currently in English.

The online manual includes sidebar navigation, page outlines, and full-text search. To preview documentation changes locally:

```sh
uv run --locked --group docs mkdocs serve
```

Open `http://127.0.0.1:8000`. The server reloads when documentation changes. Build a static site with `bash scripts/build_docs.sh`; the output is in `build/docs/`. See [Cloudflare Pages deployment](https://docs.openbacktesting.com/deployment/) for the build settings.

| Topic | Reference |
| --- | --- |
| Getting started | [First backtest](https://docs.openbacktesting.com/quickstart/) · [Example index](https://docs.openbacktesting.com/examples/) |
| Strategies and data | [Strategy lifecycle](https://docs.openbacktesting.com/guides/author/) · [Market data](https://docs.openbacktesting.com/guides/data/) · [Strategy API](https://docs.openbacktesting.com/reference/strategy/) · [Backtest API](https://docs.openbacktesting.com/reference/core/) |
| Orders and positions | [Order, Position, and Trade](https://docs.openbacktesting.com/reference/trading/) |
| Indicators | [Indicator catalog](https://docs.openbacktesting.com/reference/indicators/) |
| Execution and optimization | [Running strategies](https://docs.openbacktesting.com/guides/runtime/) · [Parameter experiments](https://docs.openbacktesting.com/guides/optimizer/) |
| Results and plotting | [Results and Portfolio](https://docs.openbacktesting.com/guides/results/) · [Plotting-data export](https://docs.openbacktesting.com/guides/plotting/) |
| Development and contributions | [Local development](docs/core/development.md) · [Contribution guide](docs/core/contributing.md) · [Current limitations](https://docs.openbacktesting.com/limitations/) |

## Scope and compatibility

- The trading model is **single asset, single settlement currency**. Portfolio reports describe one run; they are not multi-asset portfolio accounts.
- The core package provides computation and plotting data. It includes **no chart renderer, live-trading engine, code sandbox, or Pine Script converter**, and does not promise Pine-equivalent semantics. Run only trusted strategy code.
- Windows support and full Pine comparisons have not been validated. See [current limitations](https://docs.openbacktesting.com/limitations/) for execution and market-model boundaries.

The distribution and import name are both `openbacktesting`; there are no legacy-name entry points. Old module-path pickles are not migrated automatically, earlier branded archives are not guaranteed to load, and experiments created under an old execution identity must be rerun. [Migration and provenance details](https://docs.openbacktesting.com/development/#provenance-and-behavioral-boundaries).

## Local development

From a checkout, use Python **3.12–3.14** and [uv](https://docs.astral.sh/uv/getting-started/installation/):

```sh
uv sync --locked --extra test --group docs
uv run --locked python examples/advanced/native_run.py
uv run --locked python -m pytest tests/test_inputs.py -q
uv run --locked --group docs mkdocs serve
```

The last command keeps a live documentation preview at `http://127.0.0.1:8000`; use Ctrl+C to stop it. Core source is under `src/openbacktesting/`, tests under `tests/`, and the manual under `docs/core/`.

Studio has its own Python host, frontend, and tests under `studio/`. To develop it, build the interface with Node.js **22.12+**, install core and Studio in editable mode, then run the local Python host. Follow the [Studio development steps](docs/core/development.md#studio-development) for exact commands and the current frontend rebuild workflow. Core-only and documentation work do not require Node.js.

See [local development and validation](docs/core/development.md) for environment setup, focused and full checks, generated documentation, and clean package-installation checks.

## Share code and contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [contribution guide](docs/core/contributing.md) for the full workflow:

1. Search [issues](https://github.com/lucidcog/openbacktesting/issues) and [PRs](https://github.com/lucidcog/openbacktesting/pulls); discuss substantial features or compatibility changes first.
2. Fork the repository, create a focused branch from upstream `main`, and make the change with appropriate tests, examples, and documentation.
3. Run the relevant checks, inspect the staged diff, and open a PR against `lucidcog/openbacktesting:main` describing the problem, resulting behavior, and actual validation.

For bug reports or shared strategies, include a minimal reproducer, versions, settings, and small synthetic or redistributable data. Keep credentials, private datasets, generated assets, and local run history out of commits. Studio result archives can be shared separately; include source and data only when intended and permitted. Code and general documentation use English; OpenSpec planning records use Simplified Chinese. Preserve the [project license](LICENSE) and third-party notices.

## Translations

This English README is the source of truth. Translations cover Simplified Chinese, Spanish, Brazilian Portuguese, French, German, Italian, and Hindi. Use the language links above, and follow the [translation guide](docs/readme/TRANSLATING.md) when updating them. Keep commands, API identifiers, capability boundaries, and sponsor attribution consistent across languages.

## License and provenance

The project license declaration is [Apache-2.0](LICENSE). Third-party materials retain their original licensing terms, including the [indicator reference data](tests/fixtures/indicator_expansion/README.md).
