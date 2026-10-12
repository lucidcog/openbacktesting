## Purpose

确保用户仅凭当前仓库或其分发制品即可安装、运行和开发独立回测包，运行资源、示例及必要资料完整可用，并在整个抽离过程中保持源仓库内容和工作区状态不被本次操作修改。

## ADDED Requirements

### Requirement: 独立构建与安装

项目 MUST 在支持的 Python 环境中从当前仓库根目录构建发行名为 `openbacktesting` 的 wheel 与 sdist；构建、安装及运行不得依赖源仓库、父级 workspace、桌面模块或 JavaScript 工具链。初始版本 MUST 为 `0.2.0`，Python 支持范围 MUST 为 `>=3.12,<3.15`。

#### Scenario: 独立安装两种制品

- **WHEN** 在未安装旧包且无法访问源仓库的环境中分别安装 wheel 与 sdist
- **THEN** 两者均可安装，`import openbacktesting` 成功，发行版本与 `openbacktesting.__version__` 一致，最小回测成功完成

### Requirement: 运行资源与可选依赖完整

wheel MUST 携带全部运行必需资源，包括类型标记、指标与统计目录、结果 Schema 及内置样例数据。基础安装 MUST 支持不依赖可选优化器的回测；`optimize` 与 `test` extras MUST 保留相应功能边界。

#### Scenario: 从安装环境读取资源

- **WHEN** 用户离开源码目录，通过已安装包读取资源并运行内置数据示例
- **THEN** 资源读取与回测均成功，且不访问源码工作区

#### Scenario: 可选优化器依赖边界

- **WHEN** 基础安装未提供可选优化器，用户调用相应优化方法
- **THEN** 返回明确的缺少依赖错误；安装 `optimize` extra 后，相应最小优化流程可以完成

### Requirement: 开发资料形成闭包

项目及 sdist MUST 提供运行现有测试和示例所需的本地夹具、配置、文档和数据，使用说明 MUST 提供有效的独立安装、最小回测、测试与构建命令，内部链接不得指向原工程布局。

#### Scenario: 从源码分发包开展开发

- **WHEN** 开发者解压 sdist 并安装测试依赖
- **THEN** 可使用随包说明运行测试和示例，所有必需文件均在解压目录内，缺少原仓库不会造成文件定位失败

### Requirement: 源仓库只读

本次抽离 MUST 仅在当前仓库内写入和执行产生文件的操作，不得更改源仓库源码、配置、Git 状态、缓存或构建输出。

#### Scenario: 完成抽离后检查源状态

- **WHEN** 比较抽离前后的源文件摘要和工作区状态
- **THEN** 本次操作未造成任何变化；外部并发变化如实报告且不被回滚
