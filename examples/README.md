# Core 示例

写用户策略先从推荐作者脚本开始：用户以 `@backtest(...)` 声明配置，框架注入当前图表上下文并运行。高级教程展示原生调用、自定义算法与研究流程。所有示例说明与代码供人和 AI 共用，完整使用契约见[使用手册](../docs/core/index.md)，独立安装入口见[内核说明](../README.md)，来源见[清单](../source-manifest.json)。

## 按主题选择

参数实验使用 [advanced/optimizer_results.py](advanced/optimizer_results.py)：仅保留完整 Portfolio，未选 inputs 固定为当前值；支持逐份提交、取消恢复、离线重开及字段排序。

表格按学习顺序排列；路径、执行类别、推荐状态三列由检查读取。基础依赖是 core 声明的 NumPy、pandas 与固定指标后端；GOOG 为随包日线、EURUSD 为随包小时线，均本地读取，无需下载。

| 路径                                                                             | 执行类别   | 推荐状态   | 主题与前置知识                                             | 数据与额外依赖                          |
| -------------------------------------------------------------------------------- | ---------- | ---------- | ---------------------------------------------------------- | --------------------------------------- |
| [advanced/optimizer_results.py](advanced/optimizer_results.py)                   | 命令式教程 | 进阶       | 选部分 inputs、完整 Portfolio 保存与重开排序               | 内置固定行情；无                        |
| [strategies/local_value_helpers.py](strategies/local_value_helpers.py)           | 作者脚本   | 推荐       | tick 舍入与逐根渐变                                        | 宿主固定行情；无                        |
| [strategies/local_builtin_indicators.py](strategies/local_builtin_indicators.py) | 作者脚本   | 推荐       | 条件 VWAP、mode 与五项参数扩展                             | 宿主固定行情；无                        |
| [strategies/closed_trade_statistics.py](strategies/closed_trade_statistics.py)   | 作者脚本   | 推荐       | 带费用部分退出与冻结统计                                   | 宿主固定行情；无                        |
| [strategies/strategy_logs.py](strategies/strategy_logs.py)                       | 作者脚本   | 推荐       | 三级日志、error 不终止、显式异常与结束记录                 | 宿主历史行情；无                        |
| [advanced/strategy_logs.py](advanced/strategy_logs.py)                           | 命令式教程 | 进阶       | 时间、bar 与源码行、失败取回、重跑和宿主会话               | GOOG 前四根；无                         |
| [strategies/bar_states.py](strategies/bar_states.py)                             | 作者脚本   | 推荐       | 首根逐根回调、首尾状态、位置与标签、局部有效性检查         | GOOG；无                                |
| [strategies/custom_indicators.py](strategies/custom_indicators.py)               | 作者脚本   | 推荐       | 自定义函数、双参数、具名多输出与组合函数复用               | GOOG 前 120 根；无                      |
| [strategies/plotting.py](strategies/plotting.py)                                 | 作者脚本   | 推荐       | 颜色 Input、Color/字符串、透明度、主副图与逐 bar 着色      | GOOG 前 120 根；无                      |
| [advanced/portfolio_report.py](advanced/portfolio_report.py)                     | 命令式教程 | 进阶       | 全部报告区域、部分退出身份、MFE/MAE、信号与冻结JSON        | 离线固定行情；无                        |
| [advanced/plotting_export.py](advanced/plotting_export.py)                       | 命令式教程 | 进阶       | 颜色覆盖与配置重放、冻结快照、严格 JSON、信号与成交        | 可信作者脚本；无                        |
| [strategies/trading_lifecycle.py](strategies/trading_lifecycle.py)               | 作者脚本   | 推荐       | 订单事件、拒绝、分批费用、账户与期末政策                   |
| [strategies/fractional_sizing.py](strategies/fractional_sizing.py)               | 作者脚本   | 推荐       | 三种规模、默认覆盖、冻结快照、命名目标与只减仓             |
| [strategies/managed_orders.py](strategies/managed_orders.py)                     | 作者脚本   | 进阶       | 到期、混合规模 OrderRequest OCO、保护及跟踪                |
| [strategies/first_backtest.py](strategies/first_backtest.py)                     | 作者脚本   | 推荐       | 第一次回测：EMA 登记、逐步判断、装饰器声明                 | GOOG；无                                |
| [advanced/strategy_settings.py](advanced/strategy_settings.py)                   | 命令式教程 | 进阶       | 五类枚举、平铺覆盖、JSON 版本与利率重算                    | GOOG 与固定行情；无                     |
| [advanced/chart_context.py](advanced/chart_context.py)                           | 命令式教程 | 进阶       | 品种/周期与配置注入、图表当地小时、统计日界和 DST 重复小时 | 离线固定行情；无                        |
| [advanced/run_author.py](advanced/run_author.py)                                 | 命令式教程 | 进阶       | 宿主加载作者脚本并读取结果                                 | 由示例宿主提供；无                      |
| [advanced/indicator_reference.py](advanced/indicator_reference.py)               | 命令式教程 | 进阶       | 按 ID 体验指标并逐通道检查有效性                           | GOOG 与演示附加列；无                   |
| [strategies/ema_macd.py](strategies/ema_macd.py)                                 | 作者脚本   | 推荐       | 首选模板：inputs、EMA、MACD；了解 init/next                | GOOG；无                                |
| [strategies/data_sources.py](strategies/data_sources.py)                         | 作者脚本   | 推荐       | 八个行情来源、保存句柄、派生价格组合；先读首选模板         | GOOG；无                                |
| [strategies/cross_signals.py](strategies/cross_signals.py)                       | 作者脚本   | 推荐       | 交叉序列组合与 is_* 当前布尔判断；了解 init/next           | GOOG；无                                |
| [strategies/confirmed_events.py](strategies/confirmed_events.py)                 | 作者脚本   | 进阶       | 指标组合、确认事件、形态、月锚点；了解有效性与时间对齐     | GOOG；无                                |
| [strategies/ema_inputs.py](strategies/ema_inputs.py)                             | 作者脚本   | 推荐       | 内置 EMA 与 inputs；了解预热                               | GOOG；无                                |
| [strategies/all_inputs.py](strategies/all_inputs.py)                             | 作者脚本   | 推荐       | 全部九种 inputs、枚举/颜色运行值、时间与时段边界           | GOOG 前 120 根；无                      |
| [advanced/native_run.py](advanced/native_run.py)                                 | 命令式教程 | 进阶       | 原生运行、统计/权益/交易表；框架开发入口                   | GOOG；无                                |
| [advanced/composable_strategies.py](advanced/composable_strategies.py)           | 命令式教程 | 进阶       | 信号和移动止损基类；了解 super 调用顺序                    | GOOG；无                                |
| [advanced/multiple_time_frames.py](advanced/multiple_time_frames.py)             | 命令式教程 | 进阶       | 日/周内置 RSI；了解重采样、完成周期与日历假设              | GOOG；无                                |
| [advanced/parameter_optimization.py](advanced/parameter_optimization.py)         | 命令式教程 | 进阶       | 四组 grid 与参数评分表；了解原生参数                       | GOOG；SAMBO 模式需要 optimize extra     |
| [advanced/machine_learning.py](advanced/machine_learning.py)                     | 命令式教程 | 非推荐研究 | 特征列、一次训练/滚动训练；需要 ML 与时序评估知识          | EURUSD；scikit-learn，包含在 test extra |

AI 读取顺序：在本表选择主题 → 读取对应代码及必要 API 说明 → 按执行类别生成代码。普通用户策略默认复制 `strategies/`，不能把教程里的运行或优化代码复制到作者脚本顶层。策略内置指标的唯一公开登记入口为 `self.ta`，包括高级例中的 SMA；`self.ind` 仅用于用户自定义指标，不能因为示例属于高级类别就重写已有内置指标。离线 ML 特征和周线等独立日历通过公开 `indicators.compute` 复用内置算法；周线再由 `resample_apply` 对齐主日历；不能把周线直接传给绑定日线的 `self.ta`。原生优化仍可使用普通类参数。

平铺配置的完整运行见 [advanced/strategy_settings.py](advanced/strategy_settings.py)：实际覆盖五类枚举、三种佣金、两种数量、两种滑点、JSON 覆盖、类型切换缺值拒绝、None 清空及版本 2 封套；保留低层复合费用案例，并比较继承利率和显式零的统计结果。单元与示例验证由 `test_flat_backtest_settings.py`、`test_strategy_settings.py` 和 `test_examples.py` 执行。数量预算不预留费用，实际成交仍可能因资金不足被拒绝。

## 运行与验证

在仓库根目录使用 `uv sync --locked --extra test` 安装环境后，直接运行下列示例命令。sdist 用户解包后从包根目录开始，先在自己的虚拟环境 `pip install '.[test]'`，将命令中的 `uv run --locked python` 换为 `python`。wheel 不附带 examples；需取得源码或 sdist，不能假定安装 wheel 后存在这些路径。

作者脚本通过以下配方运行；替换 path 可选择任意作者脚本。`runpy` 只用于执行已信任的本地源码，不是沙箱；runtime 不提供源码加载能力。

```python
import runpy
from openbacktesting import runtime

path = "examples/strategies/ema_macd.py"
namespace = runpy.run_path(path)
schema = runtime.describe(namespace)  # 此时尚未运行回测
chart_for = runpy.run_path("examples/advanced/run_author.py")["chart_for"]
chart = chart_for(path)
result = runtime.run(namespace, **chart)
print(schema)
print(result)
```

将配方交给当前 Python 会话执行。命令式教程只有在显式运行时才计算；加载定义不会回测、优化或训练。以下命令均从上述包根目录执行：

```sh
uv run --locked python examples/advanced/strategy_logs.py
uv run --locked python examples/advanced/plotting_export.py
uv run --locked python examples/advanced/run_author.py
uv run --locked python examples/advanced/run_author.py examples/strategies/local_value_helpers.py
uv run --locked python examples/advanced/run_author.py examples/strategies/local_builtin_indicators.py
uv run --locked python examples/advanced/run_author.py examples/strategies/closed_trade_statistics.py
uv run --locked python examples/advanced/run_author.py examples/strategies/all_inputs.py
uv run --locked python examples/advanced/chart_context.py
uv run --locked python examples/advanced/strategy_settings.py
uv run --locked python examples/advanced/indicator_reference.py --indicator ta.macd
uv run --locked python examples/advanced/native_run.py
uv run --locked python examples/advanced/composable_strategies.py
uv run --locked python examples/advanced/multiple_time_frames.py
uv run --locked python examples/advanced/parameter_optimization.py
uv run --locked python examples/advanced/parameter_optimization.py --method sambo
uv run --locked python examples/advanced/machine_learning.py
```

优化默认只有四组 grid；SAMBO 最多 40 次尝试且固定种子，需要 `pip install 'openbacktesting[optimize]'`。ML 执行随机分类演示和两次完整回测，逐 bar 预测并每 20 根重训，属于慢例，需要 `pip install 'openbacktesting[test]'`；均不会自动安装依赖。

全体例子的索引、加载边界和轻量执行验证：在包根目录运行 `uv run --locked python -m pytest tests/test_examples.py`；其中名字含 `execution` 的参数化测试显示文件路径。作者例还由 `test_script_runtime.py`、`test_indicators.py`、`test_indicator_expansion.py` 保留参数与确认时点验证。ML 完整训练通过 `OPENBACKTESTING_RUN_SLOW_EXAMPLES=1 uv run --locked python -m pytest tests/test_examples.py -k slow` 显式启用；迁入的 Linux 整体教程测试继续覆盖完整入口。平台/依赖跳过会单独报告，加载成功不代表完整执行成功。

## 关键语义

- `self.open/high/low/close/volume/hl2/hlc3/hlcc4` 是只读稳定句柄，保存引用和切片仍随游标；`hlcc4=(H+L+2C)/4`。在 init 组合指标，next 用 `[-1]` 当前值、`[-2]` 前值；数据加工须在首次访问来源前完成。
- `self.data_index/df` 每次读取反映当前可见范围，保存的 pandas 对象不会自动更新；`pip` 是价格精度标量。数组转换或算术结果也不能当作稳定句柄保存。
- EMA 和日/周 RSI 统一采用内置默认算法。此前示例的首值递推 EMA、近似 RSI 已移除，旧序列和回测结果不是当前基线；周线使用周五右标签并向前填充，不承诺 Pine 多周期等价。
- ML 的随机分类准确率不是时序样本外证据；标签跨度、时序拆分与间隔仍待独立评估，因此保持非推荐研究状态。
- 每例 docstring 说明手续费、仓位、期末平仓等选择；收益输出仅是该次数据与配置的计算结果。

## 添加或修改功能

新增 core 功能必须同批新增或扩展可运行 example，同步本索引与对应执行验证，交付记录给出“功能 → 示例路径 → 验证命令与结果”。示例必须实际使用该能力，单元测试、注释或链接不能替代。允许一个示例覆盖多个相关功能；本表数量随功能增长，不固定为九例。纯内部重构不要求新建例子，公开用法变化须同步现有示例。

单文件统一顺序：中文目的/限制 → imports → 必要辅助函数 → 策略类（配置、init、next）（作者脚本以 @backtest 装饰策略，不准备行情），或受保护 main（命令式教程）。共同信息维护在本页，独有数据、参数、输出、副作用和边界就近说明。新文件或内容变化须同步来源清单目标摘要，保留原始来源身份；新增例子要加入实际执行验证集合，不能只通过语法检查。

## 旧路径迁移

以下旧文件名已迁移；不提供旧路径包装脚本。

| 旧文件名                                          | 当前路径                             |
| ------------------------------------------------- | ------------------------------------ |
| `built_in_indicators.py`                          | `strategies/ema_macd.py`             |
| `expanded_indicators.py`                          | `strategies/confirmed_events.py`     |
| `ema_inputs.py` / `advanced/custom_ema_inputs.py` | `strategies/ema_inputs.py`           |
| `Quick Start User Guide.py`                       | `advanced/native_run.py`             |
| `Multiple Time Frames.py`                         | `advanced/multiple_time_frames.py`   |
| `Parameter Heatmap & Optimization.py`             | `advanced/parameter_optimization.py` |
| `Strategies Library.py`                           | `advanced/composable_strategies.py`  |
| `Trading with Machine Learning.py`                | `advanced/machine_learning.py`       |

Portfolio完整报告：`uv run --locked python examples/advanced/portfolio_report.py`。`test_portfolio.py`与`test_examples.py`实际验证金额、状态、冻结、字段目录及图表时区桶。
