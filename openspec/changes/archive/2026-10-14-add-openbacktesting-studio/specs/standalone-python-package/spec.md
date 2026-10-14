## MODIFIED Requirements

### Requirement: Independent build and installation

核心框架 MUST 从仓库根目录构建名为 `openbacktesting` 的 wheel 和 sdist，保持支持 Python `>=3.12,<3.15`，初始版本为 `0.2.0`。核心构建、安装和运行 MUST NOT 依赖原来源仓库、父工作区、桌面模块、Studio 或 JavaScript 工具链。同仓 Studio MUST 通过独立分发包承载 Web 依赖，不改变核心独立安装能力。

#### Scenario: Install both artifacts independently

- **WHEN** 分别在没有旧包且无法访问原来源仓库的环境安装核心 wheel 和 sdist
- **THEN** 两者都安装成功，`import openbacktesting` 可用，分发版本与 `openbacktesting.__version__` 相同，最小回测完成

#### Scenario: 核心安装不要求 Studio 工程

- **WHEN** 核心包从独立产物构建或安装，且环境没有 `studio/` 或 Node.js
- **THEN** 核心构建与回测仍成功，不尝试安装 Studio 依赖或构建前端

### Requirement: Complete local development materials

核心项目和核心 sdist MUST 保留现有测试与示例所需的本地 fixtures、配置、文档和数据。说明 MUST 提供有效的独立安装、最小回测、测试与构建命令，内部链接不得依赖原项目布局。Studio 开发材料 MUST 单独组织，核心既有验证不得因缺少 Studio 源码或前端依赖失败；共享文档的相对链接与打包范围 MUST 可验证。

#### Scenario: Develop from the source distribution

- **WHEN** 开发者解压核心 sdist 并安装测试依赖
- **THEN** 可以按说明运行原有测试和示例，所需文件都在解压目录，缺少原来源仓库不造成路径解析失败

#### Scenario: Studio 开发材料不扩大核心依赖

- **WHEN** 在只具备核心开发材料的环境执行核心检查
- **THEN** 不要求构建前端，也不因为 Studio 的图表源码或 Web 工程缺失而失败
