## ADDED Requirements

### Requirement: 完整有限参数域与独立预览

Studio MUST 在 Code 后提供 Optimizer 标签页，使用现有 shadcn 设计。参数域 MUST 支持框架九种输入类型的有限 Values，以及 int／float／price 的 Range；未选择参数保留当前值。约束 MUST 使用快照中的命名函数。预览 MUST 验证并固定源码、数据和执行身份，不能执行策略 init／next；Start MUST 是独立操作。

#### Scenario: 预览混合类型搜索

- **WHEN** 用户选择多个参数、十进制范围和约束函数后预览
- **THEN** 保存规范化计划，显示约束执行前的组合数，且尚未产生试验执行

### Requirement: 取消续跑与工作区互斥

实验 MUST 使用独立受管进程并与普通回测共享执行槽。取消 MUST 支持协作终止和超时进程清理。恢复 MUST 校验冻结的源码、数据、配置和环境身份；失败试验 MUST 保留，不自动重试。

#### Scenario: 取消后当前文件变化

- **WHEN** 用户取消实验、修改工作区文件并恢复旧实验
- **THEN** 使用旧实验源码和数据快照继续未完成组合，不采用当前文件

#### Scenario: 子进程启动失败

- **WHEN** 实验线程或进程无法启动
- **THEN** 实验保存失败状态、释放执行槽，允许修复环境后恢复

### Requirement: 权威结果查询与全部试验可见

结果页 MUST 暴露核心完整标量目录、单位、状态与方法，多字段排序和 eq／ne／lt／le／gt／ge／status 过滤。分页 MUST 保持核心提交水位，主动刷新才纳入新结果。全部试验页 MUST 包含成功、失败、约束跳过和尝试次数。打开报告 MUST 读取保存的完整 Portfolio；应用参数 MUST 检查 schema 并进入配置审阅，不能自动执行回测。

#### Scenario: 部分试验失败

- **WHEN** 一些候选在策略执行阶段失败
- **THEN** 其余组合继续，失败原因可见，成功 Portfolio 仍可排序、筛选和打开

### Requirement: 数据库导出与只读导入

导出 MUST 使用核心一致性 SQLite 备份。导入 MUST 验证数据库且保持仅查询能力，不能执行或恢复未提供的源码。普通只读报告 viewer MUST 不提供 Optimizer 执行路由。

#### Scenario: 导入历史优化数据库

- **WHEN** 用户导入有效 SQLite 实验结果
- **THEN** 可查询、分页、查看试验报告和再次导出，但不能 Start 或 Resume
