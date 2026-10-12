# OpenBacktesting

独立 Python 历史回测包，提供逐 bar 策略、指标、订单撮合、统计、参数优化、Portfolio 报告与纯数据绘图快照。发行名与导入名均为 `openbacktesting`，当前版本 `0.2.0`，支持 Python `>=3.12,<3.15`。

## 安装与运行

在源码仓库中：

```sh
uv sync --locked --extra test
uv run --locked python examples/advanced/run_author.py
```

在已有 Python 环境中安装本地源码或制品：

```sh
python -m pip install /path/to/openbacktesting
python -m pip install /path/to/openbacktesting-0.2.0-py3-none-any.whl
```

基础依赖为 NumPy、pandas 和固定的 `pandas-ta-classic==0.8.32`。SAMBO 优化另需 `optimize` extra；完整测试与研究示例使用 `test` extra。当前说明本地分发，不表示已发布到 PyPI。

## 最小回测

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

## 手册与开发

- [第一次回测](docs/core/quickstart.md)、[完整手册](docs/core/index.md)、[示例索引](examples/README.md)。
- [回测与策略 API](docs/core/reference/core.md)、[指标目录](docs/core/reference/indicators/index.md)、[运行与优化](docs/core/guides/runtime.md)。
- [开发和验证](docs/core/development.md)、[迁移清单](extraction-manifest.json)、[历史来源清单](source-manifest.json)。

```sh
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
uv build --no-sources
uv run --locked python scripts/check_package.py --artifact dist/openbacktesting-0.2.0-py3-none-any.whl --artifact dist/openbacktesting-0.2.0.tar.gz
```

wheel 携带全部运行源码、类型标记与 CSV/JSON 资源；sdist 还携带测试、示例、手册和本地检查工具。构建、安装和使用不需要父级 workspace 或 JavaScript 工具链。

## 身份与语义边界

本包仅使用新发行和导入身份，不提供旧名称兼容入口。旧模块路径 pickle 不自动迁移，带旧品牌协议标识的存档不保证可直接读取，旧实验不能按新执行身份续跑；需要重新运行生成新身份数据。新包保持迁入快照的 API 签名与计算语义。

本包输出计算结果与绘图数据，不包含渲染器、脚本沙箱或 Pine 转换器，不承诺 Pine 等价语义；详细边界见[当前限制](docs/core/limitations.md)。

## 原生结果字段

原生 `run()` 返回 pandas Series，字段为：

`Start`、`End`、`Duration`、`Exposure Time [%]`、`Equity Final [$]`、`Equity Peak [$]`、`Return [%]`、`Buy & Hold Return [%]`、`Return (Ann.) [%]`、`Volatility (Ann.) [%]`、`CAGR [%]`、`Sharpe Ratio`、`Sortino Ratio`、`Calmar Ratio`、`Alpha [%]`、`Beta`、`Max. Drawdown [%]`、`Avg. Drawdown [%]`、`Max. Drawdown Duration`、`Avg. Drawdown Duration`、`# Trades`、`Win Rate [%]`、`Best Trade [%]`、`Worst Trade [%]`、`Avg. Trade [%]`、`Max. Trade Duration`、`Avg. Trade Duration`、`Profit Factor`、`Expectancy [%]`、`SQN`、`Kelly Criterion`、`_strategy`、`_equity_curve`、`_trades`、`_orders`、`_order_sizing`、`_order_events`、`_fills`、`_trade_allocations`、`_positions`、`_account_curve`、`_final_account`、`_open_trades`、`Commissions [$]`、`# Closed Lots`。

带下划线字段是原生诊断数据，尚不是稳定的跨语言 Result Contract。详细说明见源码仓库 `docs/core/guides/results.md`。
