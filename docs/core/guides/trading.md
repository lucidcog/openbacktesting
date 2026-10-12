# 订单、撮合与仓位

0.2 支持资产数量、金额和权益百分数下单，使用独立成交账本。`buy(qty=2)` 表示买入两单位；返回 Order 仅表示请求已登记，最终状态和 Fill 才表示执行结果。字段见[交易参考](../reference/trading.md)。

## 单位与预算

`InstrumentSpec` 从 `openbacktesting.broker` 导入。默认 `quantity_step=1`、最小数量等于步长、`price_tick=None`、`min_notional=0`；symbol/currency 是标签，不提供汇率换算。配置 `quantity_step=0.001` 后，`qty=0.1` 始终为十分之一资产单位，行情与指标不缩放。

直接数量、limit/stop/sl/tp 必须符合显式网格；金额／百分数、默认固定量及预算函数允许向零取整。OHLC 必须有限且为正，索引必须递增且唯一；配置 tick 后行情也必须在网格上。数据的 `pip` 不是交易所规则。只减仓允许低于最低开仓金额的尾仓退出。

`openbacktesting.strategy.sizing` 提供纯函数，返回冻结的 `SizingDecision(qty, reference_price, estimated_cost, reason, budget)`：

| 函数              | 预算含义                                                             |
| ----------------- | -------------------------------------------------------------------- |
| `fixed_quantity`  | 固定资产数量向零归整                                                 |
| `equity_fraction` | 当前权益乘比例的名义预算，数量与每单位成本共用此预算，不按保证金放大 |
| `stop_risk`       | 权益乘风险比例，除以止损距离与每单位往返成本之和                     |

成本估计由调用者提供 `cost_per_unit`，不是对未来费用或成交价的保证。零数量决策附带最低数量/金额原因，调用方应跳过下单。非正权益、错误止损方向或零距离报错。权益10000、风险比例0.01、入场100、止损95、零成本时，计划20单位；跳空仍可能损失超过100。

## 下单规模与默认数量

普通 `buy/sell` 支持互斥的 `qty`、`amount`、`percent`：

```python
self.buy(qty=0.2)        # 真实资产数量，严格符合品种步长。
self.buy(amount=2000)    # 账户结算币种的名义金额，不含费用。
self.buy(percent=20)     # 请求时权益的 20%，不是可用现金或目标仓位。
self.sell(qty=0.2, reduce_only=True)
```

三者必须为正有限数，不能为 bool 或显式 None；percent 范围为 (0,100]。同时给多个参数会报错，不设优先级。只有三者全部省略才读取默认设置；`reduce_only=True` 必须显式给 qty，不能使用金额、百分数或默认数量。普通反向订单的规模是增量，不自动加上原仓位。

作者使用 `default_qty_type=QuantityType.FIXED` 或 `QuantityType.PERCENT_OF_EQUITY`，配合 `default_qty_value`；枚举从包根导入。默认值 None 表示必须显式给一种规模；权益数量用百分数 (0,100]，20 表示 20%。例如 `@backtest(default_qty_type=QuantityType.PERCENT_OF_EQUITY, default_qty_value=20)` 后，`self.buy()` 使用默认 20%，`self.buy(amount=500)` 则覆盖默认值。宿主覆盖类型时须同时给数值，None 可清空数量。低层 `Backtest` 保留 `DefaultOrderSize("fixed", value)` 和 `DefaultOrderSize("equity_fraction", value)`；后者使用小数 (0,1]。

金额／百分数预算在允许下单阶段按请求时 Close 和权益换算；限价／止损单也使用 Close，不按 margin 放大、不扣除挂单、不预留费用。框架按实际品种步长向零归整，在登记前拒绝零数量或低于最低金额的预算，错误原因包括 below_min_quantity/below_min_notional。显式 qty 严格校验网格，不静默归整；默认固定量允许归整。失败不撤原单、不修改账本。等待执行时不回算数量；费用、滑点或跳空可能导致资金不足被拒绝，amount 不保证实际成交金额等于预算。

普通订单的只读 `order.sizing` 是提交前冻结的 `OrderSizingSnapshot`，保存 mode、source、value、equity、reference_price、budget、qty。source 区分 explicit/default；qty 模式的 budget 为 None。只减仓仍保存请求量，实际成交可能更少。内部目标、批次退出、保护单和期末清算的 sizing 为 None。结果用 `_order_sizing` 按 order_id 关联，详见[结果指南](results.md)。

`equity_fraction` 和 `stop_risk` 继续用于独立预算分析和自定义成本估计，普通下单无需先调用。`order_target_percent(target=0.2)`、`set_trailing_stop(percent=0.1)`、旧预算工具及低层 equity_fraction 默认量仍用小数；只有新下单 percent 和作者默认数量用百分数。见[分数数量作者脚本](../../../examples/strategies/fractional_sizing.py)及[宿主覆盖与拒绝示例](../../../examples/advanced/strategy_settings.py)。

## 请求、成交与批次

- Order 有稳定 `order_id`、不可变 `request` 和冻结 `snapshot`。状态为 Submitted、Accepted、PartiallyFilled、Filled、Canceled、Expired、Rejected；终态不可重新打开，重复取消终态幂等。Accepted 不预留资金。
- 每次实际执行产生一个 Fill，费用只收一次；一个反转 Fill 可关闭多个 FIFO 批次并开立一个剩余批次。普通反转先试算整单，拒绝不允许留下部分平仓。
- Trade 是可单独管理的开仓批次，有 `trade_id` 和入场 Fill 身份。部分退出保留批次身份，并产生独立关闭片段；入场固定费按退出数量分摊，尾片段拿剩余费用，不重新调用入场费用模型。
- `sell(qty=10, reduce_only=True)` 最多减掉实际可用数量，余量记录 Partial 后取消；无可减仓位则取消为 `no_position`。对冲模式的退出必须绑定批次。

`Trade.close(qty=...)` 与 `Trade.close(portion=...)` 互斥，默认全部；比例向零归整，归零报错。`close_position()` 和 `position.close()` 逐批次提交退出，返回有序元组；空仓为空元组。`self.close` 仍是行情句柄。

`order_target_quantity(target=...)`、`order_target_value(target=...)`、`order_target_percent(target=...)` 仅支持净额模式。三个方法均显式接受命名参数 target、limit、stop、sl、tp、tag、reduce_only、expires_at、valid_bars，不接受位置参数或 conditions 字典。value/percent 用请求时 Close/权益换算并固定数量；同目标和条件的未完成订单复用，变化目标撤旧后按实际持仓计算差额。存在普通入场或手动退出挂单时，报 `conflicting_pending_order`；保护单可以并存。目标单成交前仍检查购买力，不保证跳空后权重等于目标。

无差额返回 None、目标去重和撤旧之前，均校验价格值域/网格、期限、标签及严格 bool 类型的 reduce_only。省略可选参数与显式提供 None/False 等价；非法替换保留原目标单。只有非零差额才按实际买卖方向检查 SL/TP 关系；合法无差额可撤销旧目标单，但不会构造零数量订单。

## 账户不变量

单资产、单结算币种、线性保证金、合约乘数1：

- balance = 初始余额 + 已实现价格毛损益 − 全部实际费用。
- equity = balance + 未实现价格毛损益。
- margin_used = 总名义暴露 × margin；可用保证金不小于零。
- 最终空仓时 equity = balance = 初始余额 + 所有关闭片段净损益。

`account` 是冻结账户快照，balance 不是证券交收现金。`position.snapshot` 同时给净/总/多空数量、分腿均价、毛净损益和剩余入场费。双向等量时净数量为零但 `bool(position)` 仍为真；双向或空仓没有统一成本，`return_fraction=None`。`Trade.pl`、`Position.pl` 均为净损益，活跃仓位包括剩余入场费用；`return_fraction` 是小数，统计列 `ReturnPct` 也沿用小数。

`allow_short=False` 仅禁止新增空头；可选 `max_gross_exposure` 限制总名义/权益。合法减仓不被这些开仓限制阻止。若价格跳空导致资不抵债，取消挂单并执行清算，保留真实负权益；清算错误会传播，不伪造成功。

## 生命周期与期末

`init()` 预计算指标；`on_start()`、`on_finish(summary)` 每运行各一次且不可交易。每根正常 bar 先处理已有订单，再发 `on_order/on_fill` 的封闭通知批次，随后从首根开始调用 `next()`；单根输入也调用一次。指标无效不会跳过 `next()`；订单通知、保护单和跟踪更新保留原执行阶段；通知中新单最早下一根执行，不递归撮合。异常时调用结束钩子；结束钩子也失败时保留原异常并附注。

| 配置                                          | 行为                                                                                                  |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `execution_timing=ExecutionTiming.NEXT_OPEN`  | 默认；当前策略提交的请求最早下一根处理                                                                |
| `execution_timing=ExecutionTiming.SAME_CLOSE` | `next()` 新增的无条件市价单在本根 Close 阶段只处理一次；新限价单及保护单不得使用已发生的本根 High/Low |
| `end_policy=EndPolicy.MARK_TO_MARKET`         | 默认；取消挂单，保留未平仓批次并按末 Close 估值                                                       |
| `end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE`    | 先取消挂单，仅对实际持仓作末 Close 合成清算，照常收取成本                                             |

以上为作者枚举写法；低层 Backtest 仍用对应小写字符串。终止流程不重跑最后一根撮合。最后一次 `next()` 提交、尚未到达执行阶段的入场不会凭空成交。期末记独立 terminal 快照，不覆盖正常 bar 的暴露观察值。

## 到期、组合与成本

默认 GTC；`valid_bars=n` 可在提交后的第1至第n根执行，下一根开始先到期；`expires_at` 与行情索引均须带时区，等于到期时刻即失效。两者互斥。保护订单为 GTC。

`submit_oco(first=OrderRequest(...), second=OrderRequest(...))` 接收两个命名入场请求，OrderRequest 从 openbacktesting.broker 导入。side 必填；qty/amount/percent 必须显式三选一，不继承默认设置；其余接受 limit、stop、sl、tp、tag、expires_at、valid_bars。未选的规模属性为 None。构造没有交易副作用，可在 init 准备并跨运行复用，标签在构造时固化。

```python
# init 中准备；此时没有读取账户或行情。
self.long_entry = OrderRequest(side="buy", percent=20, stop=105)
self.short_entry = OrderRequest(side="sell", amount=2000, stop=95)
# next 中提交；两成员使用同一时刻的账户、Close 和品种。
group = self.submit_oco(first=self.long_entry, second=self.short_entry)
```

品种网格、行情时区和保护方向在提交时校验；两成员分别解析为固定数量，先完成全部验证再原子登记和发布快照。第二笔失败不会登记第一笔或消耗订单／组身份。成员之间不拆分、叠加扣除或预留预算，成交时仍独立检查购买力；混合模式不改变执行阶段。
两个成员允许同向或反向。任一成员成交、取消、到期或拒绝都会结束另一成员；同 bar 双触发时 first 优先，记录 `ambiguous_oco_bar`。组可查询历史和取消；取消保护组不会自动平仓。

初始 `sl/tp` 在实际入场后激活。普通 next-open 市价入场的保护可检查本根剩余范围；条件入场及 same-close 入场保护延迟到下一根，并留下诊断。同 bar SL/TP 都可达时执行 SL，记录 `ambiguous_bracket_bar`，不声称推断了真实盘中顺序。部分退出会撤旧保护并按剩余数量重建。

`trade.set_trailing_stop(amount=...)` 或 `percent=...` 替换固定 SL，可保留 TP。先检查旧 stop，再按本根 Close 单调收紧，下一根生效；百分比直接使用当前价格。`TrailingStrategy` 的 ATR 不回填未来值，ATR 未预热时不设置保护。

作者以 `slippage_type=SlippageType.FIXED/BPS` 和非负 `slippage_value` 声明固定价格距离／基点滑点，0 表示关闭。spread 对每次买卖执行生效；低层 `Slippage("none")`、`Slippage("fixed", value)`、`Slippage("bps", value)` 提供确定性滑点。成本价按买上/卖下取 tick；不得越过 limit。普通市价/stop 成交限制在本根 High/Low 内；same-close 和期末合成成交允许成本价超出本根范围。费用函数必须纯粹、返回有限值；返佣允许为负，不能依靠回调副作用。

普通 buy/sell 继续使用命名参数，reduce_only 必须为 bool。tag 可以是 JSON 纯值，包括嵌套字典；它只是可选元数据，不是订单条件字典。作者 OrderRequest 不接受 reduce_only/trade_id/tag_json；已登记订单的 request 是只读规范化观察值，字段与[结果表](results.md)保持一致。

## 佣金模式与高级复合费用

作者使用 `commission_type=CommissionType.PERCENT/CASH_PER_ORDER/CASH_PER_CONTRACT` 和 `commission_value`。百分数 0.2 表示成交金额的 0.2%，范围 [-10,10)；其余为非负账户金额，分别按每次实际 Fill 或每实际资产单位收取。一个反转 Fill 仍只收一次固定费用，随后按数量分摊。作者入口一次只启用一种模式。

低层 `Backtest` 的 `Commission(fixed=0.0, relative=0.0, per_unit=0.0)` 从 openbacktesting.broker 导入，每个实际 Fill 费用为 `fixed + abs(qty) * price * relative + abs(qty) * per_unit`。固定额与每单位费非负，比例在 [-0.1,0.1)；数值必须有限且不能为 bool。relative=0.002 表示 0.2%，per_unit 是每实际资产单位费用，合约乘数仍为 1。

低层数字和二元组佣金继续可用。购买力试算不扣费，实际 Fill 只收费一次，反转或分批退出继续分摊；所有清算路径使用同一公式。snapshot/from_snapshot 以 kind=linear、version=1 和三个完整字段严格恢复，未知字段或版本拒绝。任意 callable 仍仅限低层，且保留不可重建诊断。复合费用实际运行见[设置教程](../../../examples/advanced/strategy_settings.py)，作者模式见[每单位费用示例](../../../examples/strategies/trading_lifecycle.py)。

## 示例与验证

| 能力                                     | 可运行示例                                                                            | 验证                                                                                           |
| ---------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 状态、费用、账户、生命周期、期末         | [trading_lifecycle.py](../../../examples/strategies/trading_lifecycle.py) | `test_order_api.py`、`test_trading_core.py`、`test_trading_regressions.py`、`test_examples.py` |
| 三模式、默认覆盖、快照、命名目标、只减仓 | [fractional_sizing.py](../../../examples/strategies/fractional_sizing.py) | 同上                                                                                           |
| 到期、混合规模 OCO、保护、跟踪、成本     | [managed_orders.py](../../../examples/strategies/managed_orders.py)       | 同上                                                                                           |

按[示例入口](../examples.md)执行。交易记录由 Python 引擎直接生成。

## 显式价格舍入与已关闭片段

`instrument.round_price_to_tick(value)` 要求有限正价和显式 `price_tick`，按十进制最近 tick 舍入，恰好半 tick 向上；结果归零、溢出或无法以 float 精确表达十进制网格时拒绝。返回值再经过原 `price` 校验。此工具只用于作者候选价，不自动修正订单，也不改变成交和保护单原有方向舍入政策。

`self.closed_trade_stats` 返回 `broker.ClosedTradeStats` 冻结快照。按已关闭片段而非唯一 `trade_id` 计数，每次部分退出单独计入；净损益包含该片段分摊的开仓和退出费用，返佣按其真实符号计入。`win_count/loss_count/even_count` 按净损益严格正、负、零划分；`winning_profit` 为正净损益之和，`losing_amount` 为非负亏损额，`net_profit` 为两者之差，`average_profit` 为净损益除片段数，`win_rate` 为 0–1 胜率。空统计的金额及次数为零，平均值与胜率为 None。

统计在关闭费用分摊后增量更新，读取不遍历历史；未平仓损益与尚未分摊的持仓开仓费不提前进入统计。`same_close` 的 next 中提交退出仍只能看到成交前事实，随后的成交通知和 on_finish 可读已完成结果。同批成交在批次结束后派送通知，因此同批通知均读取当时最新累计，不是逐事件历史快照。保存旧快照不会随成交或后续 Trade 对象修改而改变；重复运行独立。属性为保留名，不能覆盖。示例见[纯值辅助](../../../examples/strategies/local_value_helpers.py)与[关闭统计](../../../examples/strategies/closed_trade_statistics.py)。
