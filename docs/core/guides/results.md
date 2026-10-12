# 结果消费

## 参数实验的持久结果

`runtime.optimize()` 与 `optimizer.open_result()` 提供逐份完整 Portfolio 保存和只读结果集；用法见[参数实验](optimizer.md)。它只保存 Portfolio 和必要管理元数据，不保存日志或绘图；下文普通运行默认采集不受影响。

## Portfolio 完整报告

`run()`、`run_inputs()`及宿主`runtime.run()`仍返回原有pandas Series，同时在`attrs["portfolio_snapshot"]`保存不可变`PortfolioSnapshot`。运行结束冻结完整事实；`openbacktesting.portfolio.export_result(result)`或`get_snapshot(result).to_dict()`只根据冻结数据计算报告，不重跑策略。原行情、交易表、标签、导出副本随后修改不会改变快照；无需保留`_strategy`。快照的字符串内容是内部事实存储，跨语言传输应使用导出字典。

报告`schemaVersion="1.0.0"`与交易表版本4、执行政策版本2独立。`report_catalog()`返回字段、单位、方法、可用性及示例验证目录。完整示例见[Portfolio报告](../../../examples/advanced/portfolio_report.py)。宿主可以直接消费以下区域：

| 字段                              | 内容                                                                          |
| --------------------------------- | ----------------------------------------------------------------------------- |
| `run/context/semantics`           | 实际执行与输入范围、终止原因、图表时区、配置、版本和有效利率                  |
| `facts`                           | 全部订单、规模、状态事件、成交与开平分配，包括未成交请求                      |
| `trades.closedFragments/openLots` | 关闭片段与未平批次；入出场两腿、信号、价格、数量、费用、收益、持有期、MFE/MAE |
| `summary.all/long/short`          | 账户/方向贡献、交易统计、收盘路径和月度风险                                   |
| `series`                          | 有序账户观察、收盘、方向虚拟权益、两套基准、已关闭累计和保证金                |
| `analysis`                        | 信号/方向分解，日周月季年桶，分布/异常值，连胜连败，时间模式，增长/回撤区间   |
| `extensions.legacy`               | 原统计键与原口径；不替换历史计算定义                                          |

`allocation_id`是关闭片段主键；部分退出可共享`trade_id`，不能用批次ID去重交易行。数量为真实成交数量。非空字符串tag作为signal；对象tag仅读取非空字符串signal及字符串comment，其余原值保留。内部退出没有用户信号时返回null。

新指标使用`value/unit/status/reason/methodId/sampleCount/reference`；比例为小数，纳秒/超JavaScript安全整数用十进制字符串。aware时间编码UTC绝对纳秒并单独记录图表时区；naive和ordinal独立标记。无成交计数/金额为0，无样本均值为null；无亏损的PF为null+unbounded，未支持字段不能补0。

新`profitFactorMoney`按正负净金额合计相除，旧`Profit Factor`仍汇总交易收益率。月度风险以自然月账户收益、有效月利率`(1+rf)^(1/12)-1`、总体标准差/负超额平方均值和sqrt(12)年化计算；少于两月或负权益分母无效时说明不足。方向曲线使用相同初始资金加该方向实际贡献，反转与部分退出不会把未来平仓利润提前记到入场。

基准分别为`input_start_close`和`first_entry_price`，按资产数量步长向下取整，检查最小数量/名义金额，保留余款且不收费。无入场则第二套不适用。日历桶依据图表时区，缺数据桶结转并标carriedForward，首尾不完整桶标partial，实际终止之后不造桶。

MFE/MAE是持有期间的毛价格偏移，部分退出按片段数量冻结。same_close入场不使用入场前高低点，Open退出不使用退出后高低点；条件单无法恢复同根顺序时标partial下界。有序盘中路径标`sampled_bounds_v1`，完整持仓bar的高低点成组与前后端点计算下界，不虚构组内顺序。增长幅度跨过非正权益基数时，比例返回undefined而非0。Commission load、Tukey异常值、增长分段及固定路径资金需求是明确的本地方法，不声明TradingView数值认证。

当前不支持保证金追缴、TV账户资金需求/追缴清算量、跨币种换算与合约乘数；破产/end_liquidation数量单独记录。Portfolio是单资产单币种单次运行结果，不提供多资产组合账户。

全账户`compute_stats`重算保留事实、更新有效利率与legacy统计；交易子集缺乏全账户路径，清除原Portfolio并记录`portfolio_diagnostic`，不能导出伪全账户报告。内置字符串优化目标候选保持轻量路径，自定义callable可读取完整Portfolio，最终参数正式重跑保留完整事实。运行/导出均不自动写文件、请求网络或接入网页。

统计实现和新 pickle 使用 `openbacktesting.portfolio` 下的真实定义路径。`results`、`stats`、`_stats` 旧模块已移除，不提供历史统计 pickle 迁移；`lib.compute_stats` 仍是公开的重算便利入口。

## 原生结果字段

以下为 `run()` 返回的 pandas Series 字段；带下划线字段是原生诊断数据，尚不是稳定的跨语言 Result Contract。

- `Start`
- `End`
- `Duration`
- `Exposure Time [%]`
- `Equity Final [$]`
- `Equity Peak [$]`
- `Return [%]`
- `Buy & Hold Return [%]`
- `Return (Ann.) [%]`
- `Volatility (Ann.) [%]`
- `CAGR [%]`
- `Sharpe Ratio`
- `Sortino Ratio`
- `Calmar Ratio`
- `Alpha [%]`
- `Beta`
- `Max. Drawdown [%]`
- `Avg. Drawdown [%]`
- `Max. Drawdown Duration`
- `Avg. Drawdown Duration`
- `# Trades`
- `Win Rate [%]`
- `Best Trade [%]`
- `Worst Trade [%]`
- `Avg. Trade [%]`
- `Max. Trade Duration`
- `Avg. Trade Duration`
- `Profit Factor`
- `Expectancy [%]`
- `SQN`
- `Kelly Criterion`
- `_strategy`
- `_equity_curve`
- `_trades`

## 交易事实表（0.2）

结果的 `attrs.trading_schema_version=4`、`execution_policy_version="2"` 标识交易语义；包含 core 版本、instrument、执行/期末政策、保证金、成本与已有输入快照。不能重建的 callable 费用配置会记录 `commission_not_reconstructable`，不把函数名称当成可重放实现。

| 字段                 | 事实与粒度                                                                                                                               |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `_orders`            | 所有请求与最新状态，包含拒绝、取消、到期和原始 stop                                                                                      |
| `_order_sizing`      | 普通订单与 OCO 的请求规模快照，按 order_id 关联，不等于成交金额                                                                          |
| `_order_events`      | 每次状态/触发变更的冻结值与全运行 sequence                                                                                               |
| `_fills`             | 一次实际执行一行，保留方向、数量、价格、费用、阶段与原因                                                                                 |
| `_trade_allocations` | Fill 到批次的开平分配；通过 fill_id/trade_id/entry_fill_id 关联                                                                          |
| `_positions`         | 正常 bar 及独立 terminal 的总暴露、净仓、毛净损益                                                                                        |
| `_account_curve`     | 同时刻的余额、权益、费用和保证金                                                                                                         |
| `_final_account`     | 纯值最终账户字典                                                                                                                         |
| `_open_trades`       | 剩余批次、入场身份、剩余入场费与未实现损益                                                                                               |
| `_trades`            | 已关闭片段，保留 Size、Entry/ExitPrice、PnL、Commission、ReturnPct、SL/TP 等常用列并增加 allocation_id、exit_fill_id、exit_sequence 身份 |

Order.request 返回冻结的 NormalizedOrderRequest，包含规范化数量、条件和只读 reduce_only/trade_id/tag_json 等字段，tag 返回独立副本。作者输入 OrderRequest 与此观察模型分离；结果列仍从规范化模型提取，_orders 的列和值不因作者构造签名改变。同版本请求与结果支持 pickle 往返；不承诺跨版本活对象续跑。

`_order_sizing` 的固定列顺序为 order_id、mode、source、value、equity、reference_price、budget、qty；前三列为 pandas string，其余为 float64。qty 模式的 budget 为 NaN。每个带规模快照的已登记订单只有一行，取消／拒绝／到期仍保留；提交校验失败没有记录，内部目标／保护等订单没有规模行。百分数 value 使用 20 表示 20%，qty 为归整后的请求量，实际执行以 `_fills` 为准。原 `_orders/_order_events/_fills` 列和 dtype 不变；规模表延续原格式，版本4新增关闭片段的退出关联，执行政策和作者设置快照版本均不变。

空结果仍保留列。读取这些表不需要 `_strategy`；该对象仅用于 Python 调试，不属于可持久化交易协议。JSON 标签只能使用有限数、字符串、布尔、null、列表及字符串键映射，提交后与原对象隔离。

`Exposure Time [%]` 是正常 Close 快照中总数量非零的 bar 占全部输入 bar 的比例，包括未平仓及净零对冲。terminal 清算不改写最后一次暴露。`Commissions [$]` 统计全部 Fill 费用，包括尚未退出批次；`# Trades` 和胜率统计关闭片段，`# Closed Lots` 才统计完全关闭的唯一批次。

`lib.compute_stats` 全量重算可使用保存的持仓路径；仅给交易子集时缺少路径，exposure 返回 NaN，不能根据已关闭交易猜测全账户暴露。

## 统计基准与重算

每次运行的 `attrs["statistics_initial_equity"]` 保存首根撮合前的正数有限初始资金。总收益、CAGR、权益峰值与回撤均以此本金为基准；权益表仍与输入等长，不插入虚构时间点。例如本金 1000、首根扣费 10、其余价格不变，收益和最大回撤均为 -1%，权益峰值为 1000。

买入持有固定用输入首根与末根 Close 计算，与指标就绪无关。日/周/月/年重采样的首桶收益为首桶末权益除以初始资金减一（零收益也保留），后续桶用相邻末权益计算。年化与风险指标使用完整桶序列；Beta 仍只用相邻行情和账户收益。首根发生且尚未恢复的回撤也计入幅度与时长，时长从首个实际时间戳计算，单根为零。

带 `DataContext` 的运行按图表时区分组、判断星期，沿用当前年化周期推断，不另转 UTC。即使成交绝对时刻、逐 bar 权益和总收益相同，切换图表时区仍可能改变每日收益分组、年化收益、波动率和 Sharpe，这是与图表日期对齐的预期口径。固定同一时区时串行与并行结果一致；不要求不同时区的统计相等。图表自然日不自动代表交易所交易日，示例见[图表上下文教程](../../../examples/advanced/chart_context.py)。

权益索引和成交时间保留本次图表时区，运行快照记录 `context.timezone`。绘图轴的 UTC 纳秒字符串标识绝对时刻，独立 `timezone` 指定显示解释；二者对应同一 bar，不修改时间戳数值以匹配钟点。

全账户重算继承初始资金，交易子集的近似权益也从该本金开始；空子集收益为零。历史结果缺少该属性时回退到第一条权益，无法还原历史未记录的首根成本；属性存在但不是正数有限数时明确拒绝。重算不改写原交易事实和运行快照。

运行设置 risk_free_rate 默认为零，采用年化小数 (-1,1)，影响旧统计风险公式以及新Portfolio月度Sharpe/Sortino，不向现金计息。每份结果的 `attrs["statistics_risk_free_rate"]` 表示本份统计的有效基准，runtime 的 `backtest_snapshot.settings` 保留原始运行设置。

`lib.compute_stats` 省略利率时继承最近一次统计值；旧结果没有键时用零，键存在但非法时拒绝。显式 `risk_free_rate=0.0` 覆盖，None 无效。连续重算继承最新基准，但不改写原运行快照，不修改源结果或重新收费；交易子集仍受原路径估计边界约束。[可运行教程](../../../examples/advanced/strategy_settings.py)展示继承和显式覆盖。

作者的 `backtest_snapshot` 为版本 2，settings 保留 16 个平铺字段、枚举字符串与百分数值；独立的 `attrs["commission"]` 仍记录实际执行模型，不能当成作者设置传回。纯值 Commission 的费用元数据采用带 kind/version 的完整对象，不产生不可重建诊断；原数字／二元组的历史导出形态保持。新设置不改变交易表列和撮合政策版本，不表示 Pine 比率或撮合语义等价。

## 绘图数据

开启默认采集后，成功结果的 `attrs["plotting_result"]` 保存独立冻结快照。使用 `openbacktesting.plotting.export_result(result)` 导出严格 JSON 兼容字典；见[绘图指南](plotting.md)。它复用 `_fills/_account_curve` 的事实，用户标记独立于成交，不依赖 `_strategy`。

## 策略日志

`bt.get_logs()` 无参数，返回本次运行全部记录的独立 `list[dict]`；尚未运行时为 `[]`，重复查询不消费记录。成功结果的 `attrs["strategy_logs"]` 为内容一致的独立副本，不改变统计键、不依赖 `_strategy`。异常后仍可读取已经写入的日志，包括 on_finish 输出；运行参数或构造失败通常为空。run/run_inputs/optimize 的新调用会清空前次记录，已经返回的副本保持不变。

| 字段                         | 含义                                                                                 |
| ---------------------------- | ------------------------------------------------------------------------------------ |
| `sequence`                   | 每次运行从 1 开始的成功追加序号，唯一排序依据                                        |
| `level`、`message`           | info/warning/error 及原始字符串；时间和代码位置不拼入正文                            |
| `phase`                      | init/on_start/next/on_order/on_fill/terminal_order/terminal_fill/on_finish           |
| `bar_index`                  | 当前输入零起点位置；无当前 bar 时为 None                                             |
| `bar_time`                   | 输入日期标签的 ISO 8601 字符串，保留精度与已有偏移；非日期索引或无当前 bar 为 None   |
| `time_kind`                  | aware-datetime/naive-datetime/ordinal/none，区分有时区、无时区、普通索引及无当前 bar |
| `recorded_at`                | UTC 系统时间，带 +00:00，微秒精度；重跑可变化，不用于行情排序                        |
| `source_file`、`source_line` | 实际调用的文件/虚拟标识与从 1 开始的代码行；无法获取时同为 None                      |

bar_time 忠实记录运行索引标签；带 context 时已转换为图表时区，保留当地偏移，不保证是开盘时间，也不减周期。recorded_at 始终是系统 UTC 记录时间，不用于对齐历史 bar。提前破产的 terminal 日志关联实际处理位置，不关联未执行末根。源码位置对应实际运行代码；动态代码可能为 `<string>`，文件后来被修改也不会改写旧记录。控制台展示及编辑器快照映射由未来宿主实现。

默认全量保留，超过 10,000 条仍不截断，内存随条数、消息大小和导出副本增长；不提供磁盘存储、分页或进程强杀后的恢复。优化只保留最终参数正式重跑的日志；候选、其他策略和全局 Python 输出不并入本列表。完整运行配方见[消费示例](../../../examples/advanced/strategy_logs.py)。

## 运行中关闭片段累计

`Strategy.closed_trade_stats` 是冻结的 `ClosedTradeStats` 纯值，可在回调与结束后读取及 pickle 传递。它累计已完成的关闭片段净损益，已含分摊费用；部分退出分别计数，空平均值与胜率为 None。每次运行从零开始，异常之前已经发生的关闭仍保留。它不替代结果表，也不含当前未平仓浮动损益；`winning_profit` 并非未扣费毛利润。与 `_trades.PnL` 的独立聚合核对见[关闭统计示例](../../../examples/strategies/closed_trade_statistics.py)，精确字段和时序见[交易指南](trading.md#显式价格舍入与已关闭片段)。
