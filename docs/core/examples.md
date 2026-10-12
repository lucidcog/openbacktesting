# 示例与执行证据

## 参数实验结果库

以下教程实际运行选择性参数穷举、逐份保存、取消恢复和两种排序；只保留 Portfolio。

[完整源码](../../examples/advanced/optimizer_results.py)

选择索引直接包含原始 README；完整代码来自受测文件。

[示例索引](../../examples/README.md)

## strategies/ema_macd.py

[完整源码](../../examples/strategies/ema_macd.py)

## strategies/custom_indicators.py

[完整源码](../../examples/strategies/custom_indicators.py)

## strategies/data_sources.py

[完整源码](../../examples/strategies/data_sources.py)

## strategies/confirmed_events.py

[完整源码](../../examples/strategies/confirmed_events.py)

## strategies/ema_inputs.py

[完整源码](../../examples/strategies/ema_inputs.py)

## strategies/all_inputs.py

[完整源码](../../examples/strategies/all_inputs.py)

## advanced/native_run.py

[完整源码](../../examples/advanced/native_run.py)

## advanced/composable_strategies.py

[完整源码](../../examples/advanced/composable_strategies.py)

## advanced/multiple_time_frames.py

[完整源码](../../examples/advanced/multiple_time_frames.py)

## advanced/parameter_optimization.py

[完整源码](../../examples/advanced/parameter_optimization.py)

## advanced/machine_learning.py

[完整源码](../../examples/advanced/machine_learning.py)

## strategies/cross_signals.py

[完整源码](../../examples/strategies/cross_signals.py)

## 第一次回测与指标试用

### 最小作者策略

[完整源码](../../examples/strategies/first_backtest.py)

### 宿主运行入口

[完整源码](../../examples/advanced/run_author.py)

### 逐指标试用

[完整源码](../../examples/advanced/indicator_reference.py)

## 交易生命周期与费用

[完整源码](../../examples/strategies/trading_lifecycle.py)

## 原生分数与目标仓位

三模式、显式覆盖默认量、冻结规模快照及原有预算工具；金额／比例挂单在演示后撤销。

[完整源码](../../examples/strategies/fractional_sizing.py)

## 到期与组合订单

init 构造混合 percent/amount 意图，提交时统一换算，保留 OCO 互斥和保护终态。

[完整源码](../../examples/strategies/managed_orders.py)

## 绘图声明与宿主导出

[完整源码](../../examples/strategies/plotting.py)

[完整源码](../../examples/advanced/plotting_export.py)

## 图表上下文与声明覆盖

[完整源码](../../examples/advanced/chart_context.py)

## 策略设置与统计重算

教程覆盖五类枚举、三种佣金、两种数量、两种滑点、JSON 覆盖／版本验证、类型切换拒绝和清空，并区分作者单模式费用与低层复合费用；执行验证见 `test_examples.py`。

[完整源码](../../examples/advanced/strategy_settings.py)

## 首末根状态与位置

[完整源码](../../examples/strategies/bar_states.py)

## 策略日志与失败取回

[完整源码](../../examples/strategies/strategy_logs.py)

[完整源码](../../examples/advanced/strategy_logs.py)

## 本地内置能力

三例分别演示显式价格舍入/颜色、八项指标入口与带费用关闭片段统计；统一由宿主注入行情和规格。

[完整源码](../../examples/strategies/local_value_helpers.py)

[完整源码](../../examples/strategies/local_builtin_indicators.py)

[完整源码](../../examples/strategies/closed_trade_statistics.py)

## Portfolio 全部报告区域

部分退出、剩余批次、信号、MFE/MAE与冻结导出均由实际交易产生；示例遍历字段目录并验证全部分析区域。图表上下文示例同时核对当地日历桶。

[完整源码](../../examples/advanced/portfolio_report.py)
