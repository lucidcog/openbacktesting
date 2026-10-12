# API 分类与兼容入口

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

分类区分推荐调用、现存别名与内部依赖；当前用法见各主题指南。

| 路径 | 分类 | 原因及推荐路径 |
| --- | --- | --- |
| `openbacktesting.aggregation` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.broker` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.data` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.engine` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.engine.Backtest` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Backtest |
| `openbacktesting.engine.SharedMemoryManager` | internal | 优化器资源管理实现，用户使用 Backtest.optimize。 |
| `openbacktesting.engine.Strategy` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy |
| `openbacktesting.engine.compute_stats` | internal | 底层统计实现；用户使用 lib.compute_stats。 |
| `openbacktesting.engine.dummy_stats` | internal | 内部空统计构造。 |
| `openbacktesting.engine.patch` | internal | 内部临时属性替换工具。 |
| `openbacktesting.engine.try_` | internal | 内部异常包装工具。 |
| `openbacktesting.helpers` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.api` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.calculus` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.candles` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.common` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.cycles` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.methods` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.momentum` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.overlap` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.performance` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.registry` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.runtime` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.statistics` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.trend` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.types` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.types.IndicatorSpec.aliases` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.causal` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.default_backend` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.dtype` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.fixed` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.history_offset` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.history_sum` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.input_args` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.input_defaults` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.kind` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.minimum` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.missing_policy` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.parameters` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.reason` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.required` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.status` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.unit` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.validity` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.version` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.IndicatorSpec.windows` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.Parameter.choices` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.Parameter.maximum` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.types.Parameter.minimum` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.indicators.utility` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.volatility` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.volume` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.inputs` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.inputs.InputSpec.bindings` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.inputs.InputSpec.bounds` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.inputs.InputSpec.enum_type` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.inputs.InputSpec.metadata` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.inputs.InputSpec.options` | internal | 声明记录字段；由所属类的字段表说明，不能独立调用。 |
| `openbacktesting.lib` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.lib.Backtest` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Backtest |
| `openbacktesting.lib.FractionalBacktest` | internal | 内部保留的旧缩放入口；当前分数数量使用Backtest与InstrumentSpec。 |
| `openbacktesting.lib.FractionalBacktest.optimize` | internal | 内部保留的旧缩放入口；当前分数数量使用Backtest与InstrumentSpec。 |
| `openbacktesting.lib.FractionalBacktest.run` | internal | 内部保留的旧缩放入口；当前分数数量使用Backtest与InstrumentSpec。 |
| `openbacktesting.lib.FractionalBacktest.run_inputs` | internal | 内部保留的旧缩放入口；当前分数数量使用Backtest与InstrumentSpec。 |
| `openbacktesting.lib.SignalStrategy.ind` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.ind |
| `openbacktesting.lib.SignalStrategy.buy` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.buy |
| `openbacktesting.lib.SignalStrategy.close` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.close |
| `openbacktesting.lib.SignalStrategy.closed_trades` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.closed_trades |
| `openbacktesting.lib.SignalStrategy.data` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.data |
| `openbacktesting.lib.SignalStrategy.df` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.df |
| `openbacktesting.lib.SignalStrategy.equity` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.equity |
| `openbacktesting.lib.SignalStrategy.high` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.high |
| `openbacktesting.lib.SignalStrategy.hl2` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.hl2 |
| `openbacktesting.lib.SignalStrategy.hlc3` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.hlc3 |
| `openbacktesting.lib.SignalStrategy.hlcc4` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.hlcc4 |
| `openbacktesting.lib.SignalStrategy.init` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.init |
| `openbacktesting.lib.SignalStrategy.low` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.low |
| `openbacktesting.lib.SignalStrategy.open` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.open |
| `openbacktesting.lib.SignalStrategy.orders` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.orders |
| `openbacktesting.lib.SignalStrategy.pip` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.pip |
| `openbacktesting.lib.SignalStrategy.position` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.position |
| `openbacktesting.lib.SignalStrategy.sell` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.sell |
| `openbacktesting.lib.SignalStrategy.ta` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.ta |
| `openbacktesting.lib.SignalStrategy.trades` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.trades |
| `openbacktesting.lib.SignalStrategy.volume` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.volume |
| `openbacktesting.lib.Strategy` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy |
| `openbacktesting.lib.TrailingStrategy.ind` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.ind |
| `openbacktesting.lib.TrailingStrategy.buy` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.buy |
| `openbacktesting.lib.TrailingStrategy.close` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.close |
| `openbacktesting.lib.TrailingStrategy.closed_trades` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.closed_trades |
| `openbacktesting.lib.TrailingStrategy.data` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.data |
| `openbacktesting.lib.TrailingStrategy.df` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.df |
| `openbacktesting.lib.TrailingStrategy.equity` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.equity |
| `openbacktesting.lib.TrailingStrategy.high` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.high |
| `openbacktesting.lib.TrailingStrategy.hl2` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.hl2 |
| `openbacktesting.lib.TrailingStrategy.hlc3` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.hlc3 |
| `openbacktesting.lib.TrailingStrategy.hlcc4` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.hlcc4 |
| `openbacktesting.lib.TrailingStrategy.low` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.low |
| `openbacktesting.lib.TrailingStrategy.open` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.open |
| `openbacktesting.lib.TrailingStrategy.orders` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.orders |
| `openbacktesting.lib.TrailingStrategy.pip` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.pip |
| `openbacktesting.lib.TrailingStrategy.position` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.position |
| `openbacktesting.lib.TrailingStrategy.sell` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.sell |
| `openbacktesting.lib.TrailingStrategy.ta` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.ta |
| `openbacktesting.lib.TrailingStrategy.trades` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.trades |
| `openbacktesting.lib.TrailingStrategy.volume` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.volume |
| `openbacktesting.optimization` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.parallel` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.runtime` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.runtime.Backtest` | internal | 实现所需导入，推荐包根入口。 |
| `openbacktesting.runtime.Mapping` | internal | 实现使用的标准库类型。 |
| `openbacktesting.runtime.describe_inputs` | internal | 实现所需导入，推荐 inputs.describe。 |
| `openbacktesting.strategy` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.try_` | internal | 内部异常包装辅助函数。 |
| `openbacktesting.util` | internal | 命名空间或实现子包；按手册的推荐对象选择入口，不递归承诺全部成员稳定。 |
| `openbacktesting.indicators.predicates` | internal | 即时交叉判断的内部实现模块；公开入口为 Strategy.ta.is_*。 |
| `openbacktesting.broker.instrument` | internal | 交易核心实现依赖，不作为作者入口。 |
| `openbacktesting.broker.ledger` | internal | 交易核心实现依赖，不作为作者入口。 |
| `openbacktesting.broker.models` | internal | 交易核心实现依赖，不作为作者入口。 |
| `openbacktesting.broker.execution` | internal | 交易核心实现依赖，不作为作者入口。 |
| `openbacktesting.broker.core` | internal | 交易核心实现依赖，不作为作者入口。 |
| `openbacktesting.strategy.sizing.finite` | internal | 交易核心实现依赖，不作为作者入口。 |
| `openbacktesting.strategy.sizing.dataclass` | internal | 交易核心实现依赖，不作为作者入口。 |
| `openbacktesting.strategy.sizing.InstrumentSpec` | internal | 交易核心实现依赖，不作为作者入口。 |
| `openbacktesting.strategy.sizing.AccountSnapshot` | internal | 预算函数的快照类型依赖；推荐从broker导入。 |
| `openbacktesting.plotting.types` | internal | 绘图内部模块，不作为作者入口。 |
| `openbacktesting.plotting.encoding` | internal | 绘图内部模块，不作为作者入口。 |
| `openbacktesting.plotting.collector` | internal | 绘图内部模块，不作为作者入口。 |
| `openbacktesting.plotting` | internal | 绘图数据命名空间，公开入口见本模块参考。 |
| `openbacktesting.lib.SignalStrategy.plotting` | compatibility | 继承只读绘图入口。；openbacktesting.Strategy.plotting |
| `openbacktesting.lib.TrailingStrategy.plotting` | compatibility | 继承只读绘图入口。；openbacktesting.Strategy.plotting |
| `openbacktesting.colors` | internal | 颜色常量命名空间；公开成员单独列出。 |
| `openbacktesting.colors.annotations` | internal | Python 注解兼容标记，不是作者 API。 |
| `openbacktesting.colors.Color` | compatibility | Color 定义模块路径；推荐从包根导入。；openbacktesting.Color |
| `openbacktesting.simulation` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.DEFAULT_CACHE_BYTES` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.DataContext` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.InstrumentSpec` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.PlottingLimits` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.Strategy` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.asdict` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.declaration` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.isabstract` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.pd` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.resolve_request` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.runtime.version` | internal | 实现使用的模块或导入依赖；通过包根的公开对象使用。 |
| `openbacktesting.lib.SignalStrategy.timeframe` | compatibility | 继承 Strategy 的只读图表周期，保持同一属性对象。；openbacktesting.Strategy.timeframe |
| `openbacktesting.lib.TrailingStrategy.timeframe` | compatibility | 继承 Strategy 的只读图表周期，保持同一属性对象。；openbacktesting.Strategy.timeframe |
| `openbacktesting.broker.Commission.calculate` | internal | 撮合已校验成交值后调用的纯费用公式；作者使用配置模型，真实费用以 Fill 为准。 |
| `openbacktesting.broker.commission` | internal | 费用模型实现模块；推荐从 openbacktesting.broker 导入 Commission。 |
| `openbacktesting.lib.SignalStrategy.data_index` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.data_index |
| `openbacktesting.lib.TrailingStrategy.data_index` | compatibility | 同对象别名或继承成员，参见推荐入口的契约。；openbacktesting.Strategy.data_index |
| `openbacktesting.lib.SignalStrategy.bar_index` | compatibility | 继承 Strategy 的同一只读属性。；openbacktesting.Strategy.bar_index |
| `openbacktesting.lib.SignalStrategy.bar_state` | compatibility | 继承 Strategy 的同一只读属性。；openbacktesting.Strategy.bar_state |
| `openbacktesting.lib.TrailingStrategy.bar_index` | compatibility | 继承 Strategy 的同一只读属性。；openbacktesting.Strategy.bar_index |
| `openbacktesting.lib.TrailingStrategy.bar_state` | compatibility | 继承 Strategy 的同一只读属性。；openbacktesting.Strategy.bar_state |
| `openbacktesting.logs` | internal | 日志实现模块；作者通过 self.log，宿主通过根 RunLogs 使用。 |
| `openbacktesting.runtime.RunLogs` | compatibility | runtime 内部导入的同一对象；推荐根导出。；openbacktesting.RunLogs |
| `openbacktesting.lib.FractionalBacktest.get_logs` | internal | 内部保留的旧缩放入口；当前分数数量使用Backtest与InstrumentSpec。 |
| `openbacktesting.lib.SignalStrategy.log` | compatibility | 继承 Strategy 的同一只读属性。；openbacktesting.Strategy.log |
| `openbacktesting.lib.TrailingStrategy.log` | compatibility | 继承 Strategy 的同一只读属性。；openbacktesting.Strategy.log |
| `openbacktesting.broker.requests` | internal | 作者请求的实现模块；推荐从 broker 导入 OrderRequest。 |
| `openbacktesting.broker.models.NormalizedOrderRequest` | internal | Order.request 的只读规范化结果类型；由 Broker 创建，不作为作者构造入口。 |
| `openbacktesting.broker.sizing` | internal | Broker 层共用纯规模解析器；作者通过 buy/sell 和 OrderRequest 使用。 |
| `openbacktesting.portfolio` | internal | 报告命名空间；公开合同按其中推荐对象消费。 |
| `openbacktesting.portfolio.models` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.portfolio.metrics` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.portfolio.analysis` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.portfolio.periods` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.portfolio.builder` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.portfolio.trades` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.portfolio.snapshot` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.portfolio.rates` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.portfolio.stats` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.portfolio.helpers` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.portfolio.trading` | internal | Portfolio实现子模块，不独立承诺稳定接口。 |
| `openbacktesting.broker.observations` | internal | 只读账户与批次观察实现，不属于策略公开入口。 |
| `openbacktesting.optimizer` | internal | 参数实验装配、采集或模块组织细节；公开用法通过 optimizer 及 runtime 指定入口。 |
| `openbacktesting.runtime.CollectionPolicy` | internal | 参数实验装配、采集或模块组织细节；公开用法通过 optimizer 及 runtime 指定入口。 |
| `openbacktesting.runtime.DEFAULT_COLLECTION` | internal | 参数实验装配、采集或模块组织细节；公开用法通过 optimizer 及 runtime 指定入口。 |
| `openbacktesting.runtime.ExperimentResult` | internal | 参数实验装配、采集或模块组织细节；公开用法通过 optimizer 及 runtime 指定入口。 |
| `openbacktesting.optimizer.identity` | internal | 参数实验装配、采集或模块组织细节；公开用法通过 optimizer 及 runtime 指定入口。 |
| `openbacktesting.optimizer.models` | internal | 参数实验装配、采集或模块组织细节；公开用法通过 optimizer 及 runtime 指定入口。 |
| `openbacktesting.optimizer.query` | internal | 参数实验装配、采集或模块组织细节；公开用法通过 optimizer 及 runtime 指定入口。 |
| `openbacktesting.optimizer.runner` | internal | 参数实验装配、采集或模块组织细节；公开用法通过 optimizer 及 runtime 指定入口。 |
| `openbacktesting.optimizer.storage` | internal | 参数实验装配、采集或模块组织细节；公开用法通过 optimizer 及 runtime 指定入口。 |
| `openbacktesting.optimizer.validation` | internal | 参数实验装配、采集或模块组织细节；公开用法通过 optimizer 及 runtime 指定入口。 |
