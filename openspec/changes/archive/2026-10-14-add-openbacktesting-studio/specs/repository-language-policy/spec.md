## MODIFIED Requirements

### Requirement: English repository defaults

项目自有代码、注释、docstrings、软件包描述、默认界面、诊断和示例文案 MUST 默认使用英文，覆盖当前与归档产物。用户明确要求的中文研究与 OpenSpec 规划文档 MUST 作为登记后的语言例外保留；第三方来源文件须按可追溯原文处理。仓库说明与 OpenSpec 配置 MUST 准确表达默认规则和例外机制，既有标识符与机器可读契约不得因翻译改变。

#### Scenario: Read repository and package documentation

- **WHEN** 开发者阅读一般说明、API 文档、源码解释或包元数据
- **THEN** 项目自有默认正文为英文，明确登记的中文规划文档按授权语言呈现
- **AND** API 名、命令、数据键、链接与数值定义保持原意

#### Scenario: 用户要求中文 Studio 规划

- **WHEN** 维护本研究报告与对应 OpenSpec 提案、设计、规格、任务及归档版本
- **THEN** 正文使用简体中文并记录授权范围，不把此例外扩展为全部产品界面或代码默认中文

### Requirement: Explicit multilingual exceptions

非英文内容 MUST 具有明确的多语言、用户授权文档或第三方原文用途，并记录精确路径、用途与可验证内容身份。既有中文默认标签不能仅因历史存在就自动获准。用户输入、依赖原文与多语言测试 MUST 保留原内容；上游文件是否为原文须根据来源清单识别，本地新增内容不得借第三方目录隐匿。

#### Scenario: Preserve multilingual log content

- **WHEN** 策略输出多语言日志并进行导出或序列化
- **THEN** 文本原样往返，保留的非英文 fixture 被明确标记为该行为的验证

#### Scenario: Review a default example label

- **WHEN** 示例包含没有明确多语言用途的中文默认输入标题
- **THEN** 将默认标题改为英文并更新相关文本断言，不能借规划文档例外放行

#### Scenario: 完整上游源码含多语言文档

- **WHEN** 引入清单中有可核对的第三方原文
- **THEN** 保留原文并登记来源身份，不为通过默认语言规则改写上游内容

### Requirement: Static language enforcement

仓库检查 MUST 对未授权中文提供可操作位置并返回非零状态，覆盖受控与未忽略的交付文本、归档文档及相关分发内容，检查解码后的 JSON 与 Python 字符串。例外 MUST 精确、具理由且可审查，不能以目录通配豁免隐藏自有正文；未使用或内容身份不匹配的例外必须报告。授权整篇规划文档可通过精确文件路径与内容摘要登记，第三方原文通过逐文件来源清单登记。受保护标识符与历史二进制完整性规则 MUST 保持。

#### Scenario: Introduce escaped Chinese default copy

- **WHEN** 开发者以原文、JSON 转义或 Python 转义加入未授权中文默认文案
- **THEN** 检查失败并指出文件及位置

#### Scenario: Use an approved multilingual fixture

- **WHEN** 检查遇到精确登记的多语言 fixture
- **THEN** 仅批准的内容获准，同文件其他未经授权中文仍失败

#### Scenario: 规划文档内容或路径变化

- **WHEN** 获准中文文档更新或归档后与登记身份不同
- **THEN** 检查要求更新对应精确记录，不能通过通配整个 OpenSpec 目录规避

### Requirement: English distribution content

分发的项目自有正文与元数据 MUST 遵循英文默认，明确授权的规划文档及第三方原文按相同精确例外保留。语言处理 MUST 保持运行资源、安装行为、依赖、版本和既有多语言输入支持，不能通过删去必要材料使检查通过。

#### Scenario: Inspect wheel and source distribution

- **WHEN** 构建并检查 wheel 与 sdist
- **THEN** 项目默认正文与包描述使用英文，授权例外具有可核对记录
- **AND** 既有资源与产物完整性检查继续通过
