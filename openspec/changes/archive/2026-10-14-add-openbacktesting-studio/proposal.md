## Why

OpenBacktesting 已有独立的回测、参数、Portfolio 和图表数据接口，但尚无把本地代码编辑、参数配置、执行与结果分析连接起来的可视化工作台。新增可选的 OpenBacktesting Studio，让纯框架用户继续独立使用 Python，同时让需要图形界面的用户通过同一套计算契约完成策略研究。

本提案承接[已确认的研究与架构约束](../../../../docs/research/openbacktesting-studio-architecture.md)，基于仓库提交 `1fa4478`。本文及本变更的其他规划产物按用户要求使用简体中文；产品默认界面文案、代码注释和诊断仍遵循仓库的英文默认约定。 OpenSpec 结构关键字，以及修改既有规格时必须原样匹配的 Requirement／Scenario 名称，作为合并标识保留原文；其需求与场景正文均使用中文。

## What Changes

- 将当前仓库扩展为轻量 monorepo：根目录框架包保持原位，新增 `studio/` 下的 Python 服务与 Web 工程，分别构建、测试和分发。Studio 单向依赖框架公开接口，不恢复核心的浏览器或绘图副作用。
- 提供独立安装的 `openbacktesting-studio` 包与本地启动命令，包含已构建前端，复用用户浏览器；纯框架安装不引入 Web 依赖，Studio 运行不要求 Node.js、浏览器捆绑包或 Electron。
- 提供受工作区边界约束的本地文件编辑、内容版本检查、外部修改检测和冲突处理；保存并运行使用固定源码版本，UI 参数覆盖作为独立预设保存，不隐式改写 Python 默认值。
- 复用 `runtime.describe` 和现有参数 schema 生成完整类型化 Inputs 表单，区分策略参数、执行属性和数据配置，处理 schema 变化、校验错误和参数依赖。
- 提供本地数据配置、显式品种与周期信息、独立工作进程、执行队列、取消、异常与日志状态；不在 HTTP 进程中导入用户策略。
- 按运行保存源码、有效配置、数据身份、版本、Portfolio、PlottingResult 和诊断；提供历史查看、文件导入与只读报告模式，无须执行策略就能读取结果。
- 将实施时最新稳定版 Lightweight Charts 的完整上游源码纳入仓库，记录来源并从本地构建。所有现有绘图语义必须实现；上游能力不足时修改源码补齐，不能以“不支持”作为完成依据。
- UI 设计参考 TradingView 的工作区、参数设置和回测报告，基础组件统一采用 shadcn/ui；禁止将浏览器默认 HTML 样式作为交付界面。提供主图、副图、实际成交、权益回撤、指标状态与交易详情联动。
- 增加两包安装隔离、产物兼容、无 Node 运行、静态资源与许可证检查，并为明确授权的中文规划文档及完整第三方源码建立可审查的检查边界。

本变更不计划修改框架计算语义或已有结果字段，包含完整现有 Optimizer 的 Studio UI；不包含多次运行对比、实盘交易、远程多用户服务、完整 Python IDE 或云端数据平台。核心 API 不计划出现 **BREAKING** 变更；如实现时确需改变已有契约，应另行更新规格并说明迁移。

## Capabilities

### New Capabilities

- `studio-distribution`: 轻量 monorepo、独立包、CLI、静态资源构建与安装验证。
- `studio-workspace-host`: 本地服务、工作区权限边界、协议版本、会话与解释器选择。
- `studio-source-editor`: 文件读取、编辑、保存、外部变更、冲突和源码版本。
- `studio-strategy-configuration`: 发现策略、完整 Inputs 表单、执行设置、预设与数据配置。
- `studio-optimizer`: 完整有限参数搜索、计划预览、取消续跑、结果查询、数据库导入导出与试验报告。
- `studio-run-lifecycle`: 固定请求、独立进程、队列、取消、失败、状态恢复与日志。
- `studio-run-artifacts`: 不可变结果、运行身份、持久化、导入导出与只读查看。
- `studio-vendored-charts`: 完整图表源码纳管、本地构建、修改维护与第三方声明。
- `studio-chart-rendering`: 所有绘图语义、精确时间与事件映射、多面板和联动。
- `studio-results-report`: Portfolio 指标、权益与回撤、交易与成交明细、来源和局部缺失状态。
- `studio-ui-design`: TradingView 设计参考、shadcn/ui 基础组件、布局状态与可访问交互。

### Modified Capabilities

- `standalone-python-package`: 明确框架从根目录独立构建且无 JavaScript 依赖；新增 Studio 后仍保持原有资源、测试和安装边界。
- `package-identity`: 将现有 `openbacktesting` 身份约束明确限定于框架，并定义伴生包 `openbacktesting-studio` / `openbacktesting_studio`，保留既有数据身份。
- `repository-language-policy`: 保持产品、代码和诊断英文默认；明确允许用户授权的中文研究与 OpenSpec 产物，以及保留第三方原文的精确、可审查例外。

## Impact

- 主要新增目录：`studio/src/openbacktesting_studio/`、`studio/web/`、`studio/vendor/lightweight-charts/`、`studio/tests/`；根目录 `src/openbacktesting/` 不迁移。
- 主要复用接口：`runtime.discover/describe/run`、`inputs.describe/request_for`、`RunLogs`、`portfolio.export_result/report_catalog`、`plotting.export_result`、`DataContext`、`Timeframe`、`InstrumentSpec`。
- 构建与检查涉及根目录打包范围、Studio 自身 `pyproject.toml`、前端依赖锁文件、许可证与来源清单，以及现有包检查／语言检查的精确范围。不得把 Studio 或 vendored 源码的运行依赖加入框架基础依赖。
- 新增本地 HTTP 协议、Studio 自有的配置／运行元数据与结果容器版本；这些属于 Studio，不替代 Portfolio、PlottingResult 或输入 schema。
- 框架核心数值回归继续有效。默认验证采用相关静态检查、协议／数据转换单元测试、子进程集成与真实安装包检查；不新增浏览器 E2E、截图验收或真实浏览器流程作为默认必需任务。
- 当前阶段仅创建规划产物，不下载图表源码、不创建实现工程、不发布软件包；图表版本以实施时核验的最新稳定版本为准。
