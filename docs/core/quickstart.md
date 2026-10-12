# 第一次回测

用随包的 GOOG 历史日线完成一次本地回测：价格上穿 EMA 时买入，下穿时平仓，最后读取交易和权益。全程无需下载行情。

## 1. 准备环境

在仓库根目录运行：

```sh
uv sync --locked --extra test
```

当前验证环境为 Python 3.12。以下路径属于源码仓库；单独安装 wheel 不包含示例目录，源码或 sdist 的安装方式见[示例说明](examples.md)。

## 2. 写策略

[作者源文件](../../examples/strategies/first_backtest.py)是完整可运行定义，直接复用或复制为自己的策略文件：

[完整源码](../../examples/strategies/first_backtest.py)

- `init()` 登记 EMA，`length=20` 表示计算周期；数据和指标的最新值随后随回测游标推进。
- `next()` 在可用历史上判断交叉，下单或平仓。`is_crossover` 返回当前布尔值；历史交叉序列使用 `ta.crossover`。
- `@backtest` 保存策略默认设置。加载此文件只完成定义；下一步宿主提供行情、周期与品种规格并执行。

## 3. 运行同一策略

仍在仓库根目录运行：

```sh
uv run --locked python examples/advanced/run_author.py
```

选择索引中的其他作者示例时，把路径作为命令最后一个参数。`chart_for` 仅提供这些示例的固定行情配方；自己的宿主应注入实际图表。宿主[完整源码](../../examples/advanced/run_author.py)的执行部分如下：

[完整源码](../../examples/advanced/run_author.py)

每次加载创建新的 namespace，`runtime.describe` 无行情发现配置，`runtime.run` 接收宿主图表上下文并返回结果。只执行自己信任的本地脚本；此入口不提供沙箱。

## 4. 读取结果

命令先打印收益率、交易数和最大回撤，再打印权益曲线与交易记录的末尾几行：

| 内容     | 读取方式                      | 含义                               |
| -------- | ----------------------------- | ---------------------------------- |
| 收益率   | `result["Return [%]"]`        | 本次历史数据和配置对应的百分比收益 |
| 交易数   | `result["# Trades"]`          | 已关闭片段数量；本例启用期末清算   |
| 最大回撤 | `result["Max. Drawdown [%]"]` | 权益曲线最大回撤的百分比           |
| 权益曲线 | `result["_equity_curve"]`     | 按行情索引对齐的权益表             |
| 交易记录 | `result["_trades"]`           | 进出场、规模和盈亏等逐笔信息       |

手续费按默认 `CommissionType.PERCENT` 与 `commission_value=0.2`（0.2%）计入开平仓；结果是固定样例的计算输出，不代表未来效果。字段详情见[结果指南](guides/results.md)。

## 接下来

[策略生命周期](guides/author.md) · [参数声明](guides/inputs.md) · [EMA 参考](reference/indicators/ema.md) · [MACD 多输出](reference/indicators/macd.md) · [运行与优化](guides/runtime.md) · [完整 API](reference/core.md)

本例的加载边界和真实执行由 `tests/test_examples.py` 验证。更多边界见[当前限制](limitations.md)。
