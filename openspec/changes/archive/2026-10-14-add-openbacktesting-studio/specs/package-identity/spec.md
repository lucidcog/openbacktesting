## MODIFIED Requirements

### Requirement: Unique public identity

核心分发元数据、导入根与核心公开对象模块归属 MUST 使用 `openbacktesting`，显示名 MUST 为 `OpenBacktesting`，专用环境变量 MUST 使用 `OPENBACKTESTING_` 前缀。可选伴生分发包 MUST 使用 `openbacktesting-studio`，其自有 Python 导入根为 `openbacktesting_studio`，显示名为 `OpenBacktesting Studio`，环境变量为 `OPENBACKTESTING_STUDIO_` 前缀。两包 MUST NOT 提供旧包别名、转发模块或旧环境变量回退；第三方库保留自己的模块和许可身份，不冒充核心对象。

#### Scenario: Inspect installed package identity

- **WHEN** 用户查询核心分发元数据、导入公开对象并检查模块路径
- **THEN** 核心包与对象使用 `openbacktesting` 身份，产物中没有旧包根或兼容入口

#### Scenario: 检查可选伴生包身份

- **WHEN** 用户独立安装 Studio 并检查其入口和模块
- **THEN** Studio 使用自己的分发与导入身份，调用核心对象时仍保留核心模块归属，不复制或重命名核心类
