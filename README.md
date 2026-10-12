# OpenBacktesting

A standalone Python historical backtesting package with bar-by-bar strategies, indicators, order matching, statistics, parameter optimization, Portfolio reports, and data-only plotting snapshots. Both the distribution and import name are `openbacktesting`. Version `0.2.0` supports Python `>=3.12,<3.15`.

## Install and run

From the source repository:

```sh
uv sync --locked --extra test
uv run --locked python examples/advanced/run_author.py
```

Install local source or an artifact into an existing Python environment:

```sh
python -m pip install /path/to/openbacktesting
python -m pip install /path/to/openbacktesting-0.2.0-py3-none-any.whl
```

Base dependencies are NumPy, pandas, and pinned `pandas-ta-classic==0.8.32`. SAMBO optimization requires the `optimize` extra; full tests and research examples use the `test` extra. These instructions describe local distribution and do not imply publication on PyPI.

## Minimal backtest

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

## Manual and development

- [First backtest](docs/core/quickstart.md), [complete manual](docs/core/index.md), and [example index](examples/README.md).
- [Backtest and strategy API](docs/core/reference/core.md), [indicator catalog](docs/core/reference/indicators/index.md), and [execution and optimization](docs/core/guides/runtime.md).
- [Development and verification](docs/core/development.md), [extraction manifest](extraction-manifest.json), and [historical source manifest](source-manifest.json).

```sh
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
uv build --no-sources
uv run --locked python scripts/check_package.py --artifact dist/openbacktesting-0.2.0-py3-none-any.whl --artifact dist/openbacktesting-0.2.0.tar.gz
```

The wheel includes all runtime source, type markers, and CSV/JSON resources. The sdist also includes tests, examples, the manual, repository instructions, OpenSpec records, and local verification tools. Building, installing, and using the package require no parent workspace or JavaScript toolchain.

## Identity and semantic boundaries

This package uses only its new distribution and import identity and provides no legacy-name entry points. Pickles using old module paths are not migrated automatically, archives with former branded protocol identifiers are not guaranteed to load, and old experiments cannot resume under the new execution identity. Rerun them to generate data with the new identity. Public API signatures and computational semantics are preserved from the extracted snapshot.

The package returns computation results and plotting data. It includes no renderer, script sandbox, or Pine converter and does not promise Pine-equivalent semantics. See [current limitations](docs/core/limitations.md).

Repository code, comments, docstrings, documentation, and project-authored messages default to English. Intentional multilingual copy and its regression fixtures retain their languages. Diagnostics previously written in Chinese now use English; consumers matching message text must update, while exception types and rejection conditions remain stable. Translated example titles and strategy source can change schema or execution fingerprints; identity validation remains enforced.

## Native result fields

Native `run()` returns a pandas Series with these fields:

`Start`, `End`, `Duration`, `Exposure Time [%]`, `Equity Final [$]`, `Equity Peak [$]`, `Return [%]`, `Buy & Hold Return [%]`, `Return (Ann.) [%]`, `Volatility (Ann.) [%]`, `CAGR [%]`, `Sharpe Ratio`, `Sortino Ratio`, `Calmar Ratio`, `Alpha [%]`, `Beta`, `Max. Drawdown [%]`, `Avg. Drawdown [%]`, `Max. Drawdown Duration`, `Avg. Drawdown Duration`, `# Trades`, `Win Rate [%]`, `Best Trade [%]`, `Worst Trade [%]`, `Avg. Trade [%]`, `Max. Trade Duration`, `Avg. Trade Duration`, `Profit Factor`, `Expectancy [%]`, `SQN`, `Kelly Criterion`, `_strategy`, `_equity_curve`, `_trades`, `_orders`, `_order_sizing`, `_order_events`, `_fills`, `_trade_allocations`, `_positions`, `_account_curve`, `_final_account`, `_open_trades`, `Commissions [$]`, `# Closed Lots`.

Underscored fields contain native diagnostic data and do not yet form a stable cross-language Result Contract. See `docs/core/guides/results.md` in the source repository.
