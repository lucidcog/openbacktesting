## Purpose

定义 Studio 在同一仓库中的独立分发、安装和启动体验，使框架用户不承担 Web 依赖，同时确保 Studio 用户无需前端开发环境即可在本地使用完整界面，并能验证实际安装包与源码构建之间的关系。

## ADDED Requirements

### Requirement: 框架与工作台独立安装

系统 MUST 分别提供 `openbacktesting` 与 `openbacktesting-studio` 分发包。Studio MUST 声明兼容的框架依赖，不复制框架代码；框架基础安装 MUST NOT 引入 Studio、Web 服务或前端资源。

#### Scenario: 仅安装框架

- **WHEN** 用户在干净环境中只安装 `openbacktesting`
- **THEN** 用户可以运行原有回测与导出接口，环境中不因该安装出现 Studio 包或其 Web 依赖

#### Scenario: 安装工作台

- **WHEN** 用户安装 Studio 且尚未安装框架
- **THEN** 包管理器安装兼容的框架版本，安装后的 Studio 可以发现其版本并调用公开接口
- **AND** 依赖不满足时显示冲突，不通过复制源码规避版本要求

### Requirement: 构建产物具有清晰边界

两包 MUST 分别生成 wheel 和 sdist。核心产物 MUST 保持现有资源与开发材料，不包含 Studio 运行依赖或 vendored 图表树；Studio 产物 MUST 包含正常启动所需前端资源、来源标识与第三方声明。

#### Scenario: 检查独立安装包

- **WHEN** 离开仓库分别安装两包的 wheel 和 sdist
- **THEN** 各包在自身依赖满足时可用，资源读取不依赖父工作区或源码目录
- **AND** 框架产物不意外包含 Studio 的资源，Studio 产物不重复携带框架实现

### Requirement: 用户运行不依赖前端工具链

Studio 安装与运行 MUST 不要求 Node.js、npm、`node_modules`、浏览器捆绑包或 Electron。必要的图表、编辑器 Worker、字体与图标 MUST 从本地已安装资源加载；启动 MUST 不自动下载前端。

#### Scenario: 无 Node 的离线界面

- **WHEN** 用户安装完成后在无 Node 且断网的环境中打开已保存报告
- **THEN** 本地服务能够提供完整必需静态资源，报告读取不因 CDN 或 npm 不可达而失败
- **AND** 需要网络的数据源能力被单独说明，不冒充离线可用

### Requirement: 本地启动入口与只读入口

Studio MUST 提供选择工作区、指定策略解释器、禁止自动打开浏览器和打开已保存结果的入口。默认 MUST 使用回环地址和空闲端口；端口冲突或解释器不兼容时 MUST 报错，不能终止其他服务或静默更换用户环境。

#### Scenario: 启动工作区

- **WHEN** 用户指定工作区并使用 `--no-open` 启动
- **THEN** 服务返回本地入口且不打开浏览器，不在启动时运行任何策略

#### Scenario: 打开独立结果

- **WHEN** 用户通过只读入口打开不附带策略源码的结果
- **THEN** 可以读取现有报告和图表，源码写入与运行接口不可用

### Requirement: 安装证据与体积透明

交付 MUST 分别记录分发包大小、安装体积和首屏资源量，并完成无源码目录依赖的安装验证。懒加载 MUST NOT 被描述为已经缩小安装包；未测量的容量或延迟 MUST 标为未知。

#### Scenario: 发布前检查

- **WHEN** 实施被声明完成
- **THEN** 存在两包实际安装及资源检查记录，并标明平台、环境、包版本和未执行项
