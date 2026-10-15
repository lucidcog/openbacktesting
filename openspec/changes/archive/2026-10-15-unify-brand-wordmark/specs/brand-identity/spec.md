## Purpose

为 OpenBacktesting 提供跨 Studio、Docs 网站和第一方 README 一致的文字品牌，使用户在不同主题与屏幕尺寸下都能识别产品，并通过本地资源、可访问名称和可追溯的验收记录保障展示完整性。

## ADDED Requirements

### Requirement: 一致且独立的文字品牌

系统 SHALL 在正常宽度的主要品牌入口展示单行、混合大小写的 `OpenBacktesting` 字标；同一字标在不同载体上保持字形和宽高比一致，明暗背景均清晰可辨。紧凑标识 SHALL 与完整字标具有一致的视觉语言，并限于无法合理容纳全称的入口。

#### Scenario: 跨入口识别

- **WHEN** 用户依次查看 Studio 顶栏、Docs 页头与根 README
- **THEN** 用户看到相同字形的 `OpenBacktesting` 字标，独立的 `Studio` 或说明文字不会改变主字标拼写和形状

#### Scenario: 明暗主题

- **WHEN** 用户切换受支持的浅色与深色主题
- **THEN** 品牌仍清晰可见，不出现字标与背景同色或字形变化

### Requirement: 完整覆盖第一方品牌入口

交付 MUST 覆盖 Studio、Docs、根 README、现有七种语言 README 和 Studio README 的主要品牌展示，配置 Studio 与 Docs 的品牌 favicon，并更新现行文档截图中仍展示旧品牌的内容。交付 MUST 提供展示清单，对额外发现的第一方品牌入口记录处理结果。

#### Scenario: README 使用品牌资产

- **WHEN** 用户打开任一受支持 README
- **THEN** 品牌图片路径有效、名称可识别，语义标题、语言导航和原有说明仍可用

#### Scenario: 浏览器标签

- **WHEN** 用户打开 Studio 或 Docs 页面
- **THEN** 浏览器能够加载对应品牌 favicon，且产品页面标题保持正确

#### Scenario: 文档截图一致

- **WHEN** 用户查看描述当前界面的产品截图
- **THEN** 其中可见的第一方品牌与新字标一致，截图仍真实对应所描述工作流

### Requirement: 小尺寸与相关交互保持可用

品牌展示 SHALL 在桌面与窄屏中保持比例和辨识度，不造成新增横向溢出、文字裁切或操作按钮遮挡；不足以容纳全称时 SHALL 使用紧凑标识。Docs 品牌链接 SHALL 保持返回首页的行为，其他导航和 Studio 工作区操作 SHALL 保持原有语义。

#### Scenario: 窄屏布局

- **WHEN** 用户在 320 或 375 CSS px 宽度下查看 Studio 或 Docs
- **THEN** 完整字标或紧凑标识可辨认，导航、主题及主要操作控件仍可访问

#### Scenario: 放大与导航

- **WHEN** 用户以 200% 浏览器缩放查看页面，或从 Docs 嵌套页面激活品牌首页链接
- **THEN** 品牌不遮挡相关控件，首页链接到达正确站点首页，Studio 不因品牌接入发生工作区重置

### Requirement: 无障碍名称与渲染回退

品牌入口 MUST 暴露正确且不重复的可访问名称，原有链接保持键盘可达；README MUST 保留文本品牌名称，并在主题图片选择不受支持时提供可读回退。

#### Scenario: 辅助技术读取

- **WHEN** 用户通过屏幕阅读器或键盘访问品牌入口
- **THEN** 可识别产品名称和适用的首页链接，装饰图形不会造成重复朗读，焦点可见

#### Scenario: README 主题回退

- **WHEN** Markdown 渲染器不支持主题图片选择
- **THEN** 默认图片或文本回退仍能清楚表示 OpenBacktesting，且正文与导航不受影响

### Requirement: 资产可用性与第三方身份边界

产品 MUST 从本地构建产物加载品牌资产，完整字标不得依赖额外的远程字体或服务；资产来源、版本及授权 MUST 可追溯。替换 MUST 保留 Pineify、TradingView 归因及 vendor 素材的第三方身份，不把它们替换为第一方标识。

#### Scenario: 本地与安装产物

- **WHEN** 用户在无外部网络的环境启动已构建或已安装的 Studio，或访问包含完整资源的 Docs 构建
- **THEN** 品牌资产可加载且形状正确，无额外远程品牌依赖

#### Scenario: 同页第三方标识

- **WHEN** 页面同时展示第一方字标、赞助商或图表归因
- **THEN** OpenBacktesting 使用新品牌，第三方标识及其原有归因链接保持正确

### Requirement: 浏览器验收证据

由于用户明确要求浏览器验收，实施交付 MUST 通过真实浏览器验证 Studio、Docs 与 README 预览，并记录环境、渲染器、页面、视口、主题、检查结果和必要截图。验收 MUST 检查视觉效果与关键导航，不得仅凭构建成功或文件存在宣告完成；未执行或失败的验证 MUST 如实记录。

#### Scenario: 实施完成验收

- **WHEN** 交付被标记为实施完成
- **THEN** 记录包含桌面与窄屏、明暗主题、相关布局与导航、资源加载及 README 路径和回退的通过证据，展示清单无未处理的第一方入口

#### Scenario: 平台验证受限

- **WHEN** 仅完成本地 Markdown 预览而未检查 GitHub 原生渲染，或尚未部署 Docs
- **THEN** 交付明确标注验证和部署边界，不声称已经通过对应平台或线上验收
