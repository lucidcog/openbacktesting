# 参数实验与本地 Portfolio

`runtime.optimize()` 扫描选中的 inputs，固定其他当前值，把每组完整 Portfolio 生成后立即提交到一个本地 SQLite 结果库。返回 `ExperimentResult` 用于重开、筛选和排序；没有目标函数，也不自动重跑最佳参数。旧 `Backtest.optimize()` 仍是返回最佳统计的独立入口。

## 开始与搜索域

完整代码见[参数实验教程](../../../examples/advanced/optimizer_results.py)。运行：

```sh
uv run --locked python examples/advanced/optimizer_results.py --output /tmp/optimizer-demo.db
```

输出必须是新本地文件；已有实验使用 `runtime.resume_optimization()`。首版一份数据库对应一个实验，不支持网络文件系统。正常关闭后可携带结果库；运行中复制使用 `result.backup(destination)`，不能仅复制可能尚有 WAL 的主文件。

search 的键是 input 唯一 title，request 是当前 `schemaVersion/schemaHash/values`。省略 request 使用声明默认，不继承上次 run 覆盖。每组完整有效值都会保存。

| 搜索域                       | 用法与边界                                                                |
| ---------------------------- | ------------------------------------------------------------------------- |
| `Values([1, 2])`             | 既有 input 类型的有限候选；enum 可用成员或 wire 成员名                    |
| `Range(5, 25, 5)`            | int 的升序正步长格点；拒绝 bool 或小数                                    |
| `Range("0.1", "0.3", "0.1")` | float/price 使用有限十进制字符串或整数，避免二进制 float 作为精确范围输入 |

stop 仅在格点上时包含；0…1/0.3 最后一项为 0.9，start=stop 是一项。单维最多 100,000 个值，组合数最多有符号 64 位整数上限；磁盘/耗时可能更早成为限制，不代表支持跑完如此多组。空域、空搜索、非法及重复候选在运行前拒绝，不静默抽样。active 只影响展示，声明 step 不强制约束搜索步长。

可选 constraint 接收完整 **wire 值**，必须返回 bool，并提供稳定 constraint_id。False 记录跳过，异常中止；有效总数未全部检查时未知。函数不保存，恢复重新提供同摘要约束。收益偏好通过 query 过滤，不属于参数约束。

## 执行身份与恢复

宿主通过 `ExecutionIdentity(strategy_sha256, dependencies_sha256)` 声明实际已加载源码及本地依赖的 SHA256。引擎另外计算行情列/索引/类型与内容、设置、时区、品种和 Python/依赖版本身份；只接受数值、布尔和时间列，不接受 object 列。示例对自己的源码计算摘要；实际宿主须纳入相关本地模块，不能用可变路径冒充内容身份。

开始时冻结行情与设置，每组新建策略和账户；模块全局、外部文件/网络和任意 RNG 不受强隔离。身份一致不证明任意策略确定性，也不是安全沙箱。

恢复重新提供 namespace、当前 request/settings、data/context/instrument 和 identity；框架从库中读取搜索域并核对计划。仅补未派发/interrupted，成功、跳过和失败组不自动重跑。修改材料或版本须新建实验。源码/行情丢失不影响只读查看，但不能继续执行。

cancel 为无参 callable，返回 True 后不派发下一组；在途组允许完成并保存，不保证中断任意 Python 死循环。强杀后已提交组可读，未提交尝试在恢复时标 interrupted；计算完但提交前崩溃可能重跑该组。

## 只保留 Portfolio

本入口固定关闭日志和绘图采集，无附件开关。库中保留完整公开 Portfolio、参数、配置/版本身份、状态和简要错误；不保存 Strategy、pickle、标准输出、原始行情或源码全文。普通回测日志和绘图行为不变。

零交易、仅未平仓和正常破产都保留报告。成功指报告事务提交，不表示盈利或跑到行情末尾，后者看 Portfolio 的 complete/terminationReason。策略/导出失败记录后继续，存储失败停止。`OptimizationError` 含 path、experiment_id、最后已知 committed；错误状态无法写盘时会说明。

进度回调在成功提交后触发；回调异常不撤销已提交结果，会停止后续执行。结果库是进度事实来源。

## 查询与完整读取

`open_result(path)` 不加载策略。`info()` 返回分类计数和计划，`trials(limit, offset)` 浏览已访问组的实时状态，`load_portfolio(trial_id)` 校验后读取完整报告。`fields()` 提供路径、类型、单位、status、method 和建议排序方向 suggestedDirection。

- `query(order_by=["summary.all.totalReturn.value"])` 默认收益降序；`summary.all.maxDrawdownFraction.value` 及分析区正回撤默认升序，legacy 负回撤默认降序。显式 `(path, "asc"/"desc")` 可覆盖，多键按列表顺序。
- filters 为 `(path, op, value)`，op 支持 eq/ne/lt/le/gt/ge/status；筛选不删除报告。
- 缺失/null 排末，无亏损 PF 的 null+unbounded 不当无穷大；approximate 保留标记。单位/方法不一致拒绝混排，整数和纳秒编码精确比较。
- 路径分隔用点，原键中的点和反斜杠须转义，例如 `extensions.legacy.Max\. Drawdown [%].value`。数组/对象不可直接排序。
- limit 为 1…1000；cursor 固定查询与提交 watermark，新提交不插入后续页；无 cursor 重新查询刷新。并列按 ordinal 排序。

查询返回分页参数和选定标量，完整报告单独读取；保存时投影所有对象标量，不遍历数组。查询不重跑策略或按当前统计代码改写历史报告。首版支持存储格式 1、Portfolio 1.0.0；未知版本及损坏明确拒绝，不自动迁移。

## 验证边界

单测见 `tests/test_optimizer.py`，示例由 `test_examples.py` 实际执行。通过 `uv run --locked python -m pytest tests/test_optimizer.py` 验证提交、恢复、进程锁、查询及身份边界。首版串行；本次抽离不作跨机器容量或硬件断电保证。

## 包身份与既有结果

执行环境身份记录实际安装的 `openbacktesting` 版本。新身份实验支持重开、查询、排序和读取 Portfolio；带旧品牌语义标识的历史存档不保证直接读取，旧实验不能以新身份续跑，需重新运行生成数据。拒绝不匹配身份的恢复操作不会改写已提交结果。
