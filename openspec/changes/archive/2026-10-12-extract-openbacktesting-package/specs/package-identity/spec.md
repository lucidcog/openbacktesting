## Purpose

为独立回测包建立唯一且一致的发行、导入和数据身份，使用户不会因残留命名误用旧工程入口，并明确更名对对象序列化、运行环境标识及持久化数据的兼容范围。

## ADDED Requirements

### Requirement: 唯一公开身份

发行元数据、导入根及公开对象模块归属 MUST 使用 `openbacktesting`；项目展示名 MUST 为 `OpenBacktesting`，专属环境变量 MUST 使用 `OPENBACKTESTING_` 前缀。包 MUST 不提供旧包别名、转发模块或旧环境变量回退。

#### Scenario: 检查已安装包身份

- **WHEN** 用户查询发行元数据、导入公开对象并查看模块路径
- **THEN** 包与对象使用新身份，制品不包含旧包根或兼容入口

### Requirement: 交付内容无旧名称残留

当前仓库受控文件及未忽略的待纳入文件、wheel 和 sdist 的文件路径与内容 MUST 不出现用户禁止的旧项目名及旧包名，匹配时 MUST 忽略大小写。文档、OpenSpec、测试数据、清单、元数据及检查规则 MUST 同样受约束。

#### Scenario: 全范围名称检查

- **WHEN** 对项目交付文件及分发制品执行名称检查
- **THEN** 无任何禁用名称命中，不能通过文档豁免或删除检查范围内的文件来掩盖残留

### Requirement: 数据与执行身份一致

新输出、目录和 Schema 的 Portfolio 语义标识 MUST 一致使用 `openbacktesting_portfolio_v1`，本地指标后端身份 MUST 使用 `openbacktesting.numpy`；实验执行环境 MUST 记录新发行包身份。身份变更不得改变未涉及身份的数值定义和数据字段契约。

#### Scenario: 新数据持久化往返

- **WHEN** 用户生成 Portfolio 结果及优化实验，保存后重新打开，并按已有契约恢复可续跑的新实验
- **THEN** 结果通过新 Schema 校验，执行身份一致，统计数值及实验状态正确恢复

### Requirement: 序列化与历史兼容边界明确

新身份对象 MUST 支持既有可序列化对象的 pickle 往返与多进程传输。项目 MUST 明确告知旧模块路径 pickle 不自动迁移、旧品牌协议存档不保证直接读取、旧实验不以新执行身份续跑，且不得静默将不匹配的执行身份当作可恢复实验。

#### Scenario: 新身份对象跨进程使用

- **WHEN** 对公开可序列化对象执行 pickle 往返及 spawn 进程传输
- **THEN** 对象正确恢复，模块路径使用新导入根

#### Scenario: 不匹配的执行身份续跑

- **WHEN** 用户尝试以不同执行身份恢复既有实验
- **THEN** 按身份校验规则拒绝续跑，并保留已有实验数据
