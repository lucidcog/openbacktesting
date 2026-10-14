## Purpose

定义以 Portfolio 为唯一计算依据的报告层级、指标格式、权益路径、交易与成交详情及来源展示，使用户能理解结果与执行假设之间的关系，并在无交易、提前终止或缺少图表时仍获得准确可用的报告。

## ADDED Requirements

### Requirement: 指标来源单位与状态完整

报告 MUST 使用公开 Portfolio 指标及字段目录，不在 UI 重算账务或替换统计方法。每个指标 MUST 正确解释 value、unit、status、reason 与 methodId；未定义值显示缺失与原因，不能当作零或无穷大。

#### Scenario: 没有亏损导致比率未定义

- **WHEN** 利润因子等指标的状态为 undefined
- **THEN** 显示缺失标记与原因，不显示零或虚构有效值

#### Scenario: 比例与原生百分数混合

- **WHEN** 来源同时有小数比例和百分点统计
- **THEN** 按各自单位格式化，不多乘或少乘一百

### Requirement: 报告层级与方向口径明确

报告 MUST 提供概要、详细绩效、交易和配置来源层级，支持现有 all／long／short 指标。方向贡献 MUST 按框架方法解释，不能暗示为独立资金账户。展示标签与 TradingView 相似时 MUST 不宣称计算口径自动一致。

#### Scenario: 切换多空统计

- **WHEN** 用户查看 long 或 short 指标
- **THEN** 读取对应方向数据并保留方法说明，不把整体初始资金随意拆分后重算

### Requirement: 权益与回撤路径不虚构

默认权益图 MUST 使用收盘序列并显式处理同一末根的终止快照。无序盘中极值 MUST 作为范围信息，不按数组顺序连成路径。指标与图表采样口径不同 MUST 有说明，不能从渲染曲线重新推导权威指标。

#### Scenario: 最后一根包含终止清算

- **WHEN** 收盘与 terminal 观测共用最后时间
- **THEN** 图表使用明确的终止呈现策略，详情保留两者且不覆盖真实终值

#### Scenario: 存在 unordered 盘中极值

- **WHEN** 账户序列包含 `ordered=False` 观测
- **THEN** 不能将它们按返回顺序连接为确定盘中路径

### Requirement: 交易颗粒度与成交关联保留

报告 MUST 区分 closed fragments、open lots、orders、fills 与 allocations，保留稳定身份、费用和关联关系。分页、筛选和排序 MUST 基于原始事实；图表跳转通过身份定位，不仅依赖时间戳。

#### Scenario: 分批平仓

- **WHEN** 一个 lot 被多次部分平仓
- **THEN** 报告保留各 fragment 及关联成交，交易计数口径不默默变成 lot 数

#### Scenario: 零已平仓交易但仍持仓

- **WHEN** 已平仓数为零但有未实现盈亏
- **THEN** 显示开放持仓及其贡献，不能把非零账户收益认定为错误或清零

### Requirement: 结果与当前配置状态可辨

报告 MUST 显示 run ID、请求与实际执行范围、代码／数据／配置身份、有效成本和期末设置、环境版本及终止原因。当前编辑内容不同于展示运行时 MUST 明确标记过期。

#### Scenario: 新运行失败保留旧报告

- **WHEN** 最近一次尝试失败而界面仍显示上次成功报告
- **THEN** 明确显示旧 run ID、过期状态和新失败诊断，不能暗示旧报告是新结果

### Requirement: 部分产物仍可使用

缺图表、日志、源码或短历史 MUST 不妨碍有效 Portfolio 的读取。运行失败、数据为空、没有交易、没有该指标和结果不兼容 MUST 分别表达，不能使用同一个无信息空白状态。

#### Scenario: 回测关闭绘图采集

- **WHEN** 导入有效报告而没有 PlottingResult
- **THEN** 指标与交易仍可读，图表区域说明未提供绘图数据，不强制重跑
