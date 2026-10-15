## Why

现有测试、运行产物与文档检查尚未形成统一且持续运行的仓库反馈闭环：入口分散、第一方 CI 与浏览器验证缺失，删除 OpenSpec 文档后还留下 21 项语言例外错误。基于此前的 Harness Engineering 研究（研究目录已于归档时按用户要求删除），本变更一次覆盖已确认的 P0、P1、P2，使代理与维护者都能发现约束、执行检查、定位失败并防止重复漂移。

## What Changes

- P0：完善短 `AGENTS.md` 导航及维护文档，定义代码、契约、生成物、计划和验证的事实来源。
- P0：新增统一验证入口，支持 `docs`、`core`、`studio`、`full`，记录结构化结果、失败原因和证据；本地与第一方 CI 共用检查定义。
- P0：清理已删除文件对应的失效语言例外，保留现存中文研究、OpenSpec 和第三方来源的精确登记；不恢复已删除的历史规范。
- P1：新增三条确定性 Studio 浏览器旅程：编辑并运行、图表与报告及导入导出、失败诊断与修复后重跑；复用 Python host、真实 worker 和现有产物。浏览器验证由用户明确确认 P1，以及现有开发指南对 UI 真实浏览器验证的要求共同触发，范围仅限这三类关键交互。
- P1：为 Studio schema 生成器增加只读漂移检查；为浏览器失败保留经脱敏的最小证据，并可靠回收宿主、worker 和临时工作区。
- P2：建立基于实际导入关系的架构检查，强制 core 不依赖 Studio、Studio 消费 core 的公开边界及经确认的底层依赖规则；复用既有公开身份、序列化、schema 和来源检查。
- P2：提供只读维护扫描、可追踪的问题与质量记录、周期性 CI 扫描和可审阅的低风险修复建议，将重复失败转为规则或测试。

## Capabilities

### New Capabilities

- `repository-harness-navigation`：仓库事实地图、变更验证映射、中文计划登记与可维护的知识入口。
- `repository-verification`：统一验证配置、结果协议、只读漂移检查、基线修复及持续集成。
- `studio-browser-verification`：隔离的真实浏览器验证、三条关键旅程、失败证据与资源清理。
- `architecture-boundary-enforcement`：可执行的依赖边界、精确例外和可定位的修复诊断。
- `repository-maintenance-feedback`：只读漂移扫描、稳定问题标识、周期检查和反馈积累。

### Modified Capabilities

无。当前 `openspec/specs/` 没有可修改的现存规范；以上描述新增的开发工具行为，不重新定义交易或产品协议。

## Impact

- 主要影响 `AGENTS.md`、`docs/core/development.md`、新增维护文档、`mkdocs.yml`、`scripts/`、第一方 `.github/workflows/`、相关工具测试，以及 `studio/web/` 的浏览器开发依赖与测试配置。
- Studio 的 schema 生成器增加检查模式；只在稳定定位和诊断确有必要时增加不改变产品行为的测试接入点。不绕过 session、Origin、CSRF 或工作区锁。
- 浏览器依赖仅用于开发和 CI；core 安装及 `docs`／`core` 验证不因本变更新增 Node.js 或浏览器要求。构建与安装检查沿用双 Python 分发包边界。
- 交易数值、事件顺序、公开 API、结果 schema、运行时依赖和第三方原始身份不作语义变更；历史基线不得自动重写。
- 不新增模型运行时、云服务、自动发布或自动合并。周期维护先产出检查证据与候选修复说明；远程分支保护的实际启用需要单独核对配置，不能以新增 YAML 宣称已经生效。
