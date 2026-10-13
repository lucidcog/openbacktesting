# OpenBacktesting

**Historical backtesting in Python, from strategy rules to inspectable results.**

**English** · [简体中文](docs/readme/README.zh-CN.md) · [Español](docs/readme/README.es.md) · [Português (Brasil)](docs/readme/README.pt-BR.md) · [Français](docs/readme/README.fr.md) · [Deutsch](docs/readme/README.de.md) · [Italiano](docs/readme/README.it.md) · [हिन्दी](docs/readme/README.hi.md)

Write bar-by-bar strategies, evaluate them on historical market data, and inspect orders, trades, equity, and risk statistics. OpenBacktesting is a standalone Python package with indicators, parameter optimization, Portfolio reports, and plotting-data export.

**Python 3.12–3.14** · **Version 0.2.0** · Distribution and import: `openbacktesting`

[Quick start](#quick-start) · [Manual](docs/core/index.md) · [Examples](examples/README.md) · [Report an issue](https://github.com/lucidcog/openbacktesting/issues)

## Top sponsor — Pineify

<a href="https://pineify.app">
  <img src="docs/assets/pineify-logo.svg" alt="Pineify" width="96">
</a>

**[Pineify](https://pineify.app) is OpenBacktesting's top paid sponsor.** Its financial support helps fund this project.

Pineify provides AI-assisted Pine Script coding and a visual editor for building TradingView indicators and strategies. [Explore Pineify →](https://pineify.app)

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
uv run --locked python examples/advanced/run_author.py
```

The example uses bundled GOOG historical data; no market-data download is required. It prints return, trade count, maximum drawdown, and result tables. See [your first backtest](docs/core/quickstart.md) for a walkthrough.

To install the checked-out source into an existing Python environment instead:

```sh
python -m pip install .
```

The base dependencies are NumPy, pandas, and `pandas-ta-classic==0.8.32`. For SAMBO optimization, use `python -m pip install '.[optimize]'` or `uv sync --locked --extra optimize`. These are source-installation instructions; they do not assume a PyPI release. [Build and distribution details](docs/core/development.md).

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

`run()` returns a pandas Series. Use `result["_trades"]` for trades and `result["_equity_curve"]` for equity history. See the [results guide](docs/core/guides/results.md) for the full field list and Portfolio export; underscore-prefixed fields are native diagnostics, not a stable cross-language contract.

## Documentation

The detailed manual and examples are currently in English.

| Topic | Reference |
| --- | --- |
| Getting started | [First backtest](docs/core/quickstart.md) · [Example index](examples/README.md) |
| Strategies and data | [Strategy lifecycle](docs/core/guides/author.md) · [Market data](docs/core/guides/data.md) · [Core API](docs/core/reference/core.md) |
| Indicators | [Indicator catalog](docs/core/reference/indicators/index.md) |
| Execution and optimization | [Running strategies](docs/core/guides/runtime.md) · [Parameter experiments](docs/core/guides/optimizer.md) |
| Results and plotting | [Results and Portfolio](docs/core/guides/results.md) · [Plotting-data export](docs/core/guides/plotting.md) |
| Development | [Verification and builds](docs/core/development.md) · [Current limitations](docs/core/limitations.md) |

## Scope and compatibility

- The trading model is **single asset, single settlement currency**. Portfolio reports describe one run; they are not multi-asset portfolio accounts.
- The package provides computation and plotting data. It includes **no chart renderer, live-trading engine, code sandbox, or Pine Script converter**, and does not promise Pine-equivalent semantics. Run only trusted strategy code.
- Windows support and full Pine comparisons have not been validated. See [current limitations](docs/core/limitations.md) for execution and market-model boundaries.

The distribution and import name are both `openbacktesting`; there are no legacy-name entry points. Old module-path pickles are not migrated automatically, earlier branded archives are not guaranteed to load, and experiments created under an old execution identity must be rerun. [Migration and provenance details](docs/core/development.md#provenance-and-behavioral-boundaries).

## Support and contributing

Use [GitHub Issues](https://github.com/lucidcog/openbacktesting/issues) for bugs, questions, and feature requests. Include your Python/package versions, a minimal reproducer, and expected versus actual behavior. Contributions are welcome through [pull requests](https://github.com/lucidcog/openbacktesting/pulls).

Before submitting a code change, run:

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
```

Follow the [development guide](docs/core/development.md) for the complete checks. Public behavior changes need corresponding documentation, runnable examples, and execution validation. Code, comments, and technical documentation default to English; localized README content is intentional.

## Translations

This English README is the source of truth. Translations cover Simplified Chinese, Spanish, Brazilian Portuguese, French, German, Italian, and Hindi. Use the language links above, and follow the [translation guide](docs/readme/TRANSLATING.md) when updating them. Keep commands, API identifiers, capability boundaries, and sponsor attribution consistent across languages.

## License and provenance

The project license declaration is [Apache-2.0](LICENSE). Third-party materials retain their original licensing terms, including the [indicator reference data](tests/fixtures/indicator_expansion/README.md).

The [source manifest](source-manifest.json) records adaptations from an [AGPL-3.0 upstream snapshot](https://github.com/kernc/backtesting.py/blob/ca2e2611621e472542ba90f7243a1fa06a7d7108/LICENSE.md). The Apache-2.0 declaration does not replace those upstream terms; distributing the derived code under Apache-2.0 alone requires separate authorization. The [extraction manifest](extraction-manifest.json) records the direct source snapshot and path mappings.
