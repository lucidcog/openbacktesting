# Core 使用手册

用 Python 定义策略，在本地历史行情上回测，读取交易、权益与统计结果。当前提供独立 Python 内核，不保证 Pine 等价。

## 开始使用

[第一次回测 →](quickstart.md) 从固定离线数据开始，写出策略并通过宿主运行。

想查用法？直接进入[回测与策略 API](reference/core.md)、[指标目录](reference/indicators/index.md)或[EMA 指数移动平均](reference/indicators/ema.md)。

## 专题教程

- **写策略**：[生命周期](guides/author.md) · [读取行情](guides/data.md) · [声明参数](guides/inputs.md) · [组合指标](guides/indicators.md)
- **运行与分析**：[运行和优化](guides/runtime.md) · [订单与交易](guides/trading.md) · [读取结果](guides/results.md) · [绘图声明与导出](guides/plotting.md)
- **完整代码**：[可运行示例](examples.md)
- **参数实验**：[完整 Portfolio 保存与排序](guides/optimizer.md)

## API 参考

- [回测与策略](reference/core.md)
- [订单、仓位与交易](reference/trading.md)
- [策略组合与辅助工具](reference/helpers.md)
- [参数声明与解析](reference/inputs.md)
- [宿主运行入口](reference/runtime.md)
- [指标句柄与计算](reference/indicator-api.md)
- [绘图声明与导出](reference/plotting.md)
- [颜色值与预设](reference/colors.md)
- [Portfolio 报告与导出](reference/portfolio.md)
- [Optimizer 结果集](reference/optimizer.md)
- [按类别查找指标](reference/indicators/index.md)

## 维护与限制

[当前限制](limitations.md) · [兼容入口](reference/classification.md) · [文档维护](development.md) · [构建来源](build-info.md)


