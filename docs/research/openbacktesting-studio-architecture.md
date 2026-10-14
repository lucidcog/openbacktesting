# OpenBacktesting Studio：研究依据与架构建议

**OpenBacktesting Studio 适合作为可选的本地策略编写与分析应用的名称；现有框架已经提供了大部分执行、参数、组合报告和图表数据契约，Studio 应复用这些契约。**

研究日期：2026-10-14。仓库基线：`main` 分支上的 `a871775e81cc946978e08696dbb5a559ddf2f6ef`。本文属于研究报告，不是实施提案，也不承诺与 TradingView 功能对等。**事实**表示已查阅源码或文档确认的内容；**建议**表示设计选择；**推论**表示从事实推导出的结论；**用户约束**表示用户已明确指定、后续设计与实现必须遵守的要求。仓库内的相对路径引用均以该基线为准。

## 1. 产品边界与现有基础

**建议：**Python 框架沿用 **OpenBacktesting**，可选的浏览器应用命名为 **OpenBacktesting Studio**。“Studio”能覆盖“编辑 → 配置 → 运行 → 分析”的完整流程，比仅指向图表或报告的名称更合适。这是产品命名判断；商标和软件包名称是否可用，尚未核查。

仅使用框架和同时使用 Studio 的用户，都应获得完整、独立可用的体验：

| 使用方式 | 必须提供的体验 | 依赖约束 |
| --- | --- | --- |
| Python 脚本、Notebook、Agent、CI、其他应用 | 运行策略、查看参数定义、导出完整结果与图表数据、保存和查询实验 | 无须安装 Studio、浏览器、Web 服务或 JavaScript 环境 |
| 已保存结果的查看器 | 打开已导出的回测结果，查看报告和图表，无须执行策略源码 | 渲染过程不得导入或运行 Python 策略代码 |
| 完整的本地 Studio | 编辑真实 Python 文件，配置有类型约束的参数、数据和设置，执行回测并分析结果 | 与其他宿主程序调用相同的框架公开接口 |

完整 Studio 对应第二类用户；只读查看器是 Studio 内部有价值的能力边界，不需要第三套回测引擎。

**事实：核心框架已经独立于展示层。** `pyproject.toml` 的基础依赖只有 NumPy、pandas 和 pandas-ta-classic。测试明确要求不提供 `Backtest.plot`、不导入 Bokeh、不打开浏览器，也不产生输出文件等副作用。恢复旧渲染 API 会改变这一有意建立的边界。[软件包配置](../../pyproject.toml)、[纯结果接口的不变量](../../tests/test_result_only.py)。

| 现有公开契约 | Studio 应复用的能力 | 仍由宿主程序负责的部分 |
| --- | --- | --- |
| `runtime.discover/describe/run`、`@backtest`、`RunLogs` | 发现唯一的已装饰策略、读取默认配置、执行、保留诊断信息 | 文件和模块加载、进程管理、数据获取、持久化 |
| `inputs.describe`、`inputs.request_for`、`Backtest.run_inputs` | 有类型约束的控件，以及携带 schema 身份并经过校验的请求 | 表单交互、参数预设、过期 schema 处理 |
| `portfolio.export_result/get_snapshot/report_catalog` | 不可变的事实快照、指标、分析、单位、状态与字段目录 | 报告布局、分页、用于图表展示的数据视图 |
| `plotting.export_result` | OHLC、数据源、面板、声明的图形与实际执行记录 | 纳入并构建最新稳定版 Lightweight Charts 完整源码，完成数据映射；能力不足时修改源码补齐 |
| `runtime.optimize/resume_optimization`、`optimizer.open_result` | 保存参数实验及其排名 | 可在后续提供的实验 UI |

这些契约已记录在[运行时](../core/reference/runtime.md)、[策略参数](../core/reference/inputs.md)、[Portfolio 报告](../core/reference/portfolio.md)、[图表数据](../core/reference/plotting.md)和[优化器](../core/reference/optimizer.md)文档中。`runtime.run` 接收已加载的命名空间，需要宿主提供 `data`、`DataContext` 和 `InstrumentSpec`；它本身不负责文件执行服务。`runtime.describe` 不进入策略生命周期，但导入模块仍可能执行任意模块级 Python 代码。[运行时契约](../core/reference/runtime.md)。

## 2. backtesting.py 如何实现结果展示

本次查阅的上游版本为 **0.6.6**，提交为 [`9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d`](https://github.com/kernc/backtesting.py/tree/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d)。固定版本是为了明确研究对象：本节描述上游实现，不代表 OpenBacktesting 当前的实现。

### 执行 → 统计 → 展示

**事实：**`Backtest.run(**kwargs)` 创建数据、经纪商和策略实例，调用 `init`，逐根推进 K 线并逐步暴露指标数据，处理经纪商逻辑和 `next`，按配置处理期末平仓，最后调用 `compute_stats`。返回的 pandas Series 同时保存在 `_results` 中。[运行逻辑](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/backtesting.py#L1271-L1384)。

**事实：**`compute_stats` 构建权益与回撤数据表、已平仓交易表，计算标量统计，并将 `_strategy`、`_equity_curve` 和 `_trades` 放进结果 Series。交易表包含入场与出场的 K 线位置、价格和时间，以及数量、盈亏、佣金、收益率、持仓时长、标签和记录下来的指标值。[统计源码](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/_stats.py#L37-L187)。

**事实：**`Backtest.plot` 读取传入或最近一次运行的结果、Backtest 保存的原始 OHLC 数据，以及策略实例的 `_indicators`，然后调用 `_plotting.plot`。因此，上游渲染器依赖内存中的内部 Python 对象；OpenBacktesting 已有的公开、冻结 JSON 数据契约与之不同。[绘图调用入口](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/backtesting.py#L1740-L1769)。

### Bokeh 的图表组合与交互

**事实：**渲染器纵向排列多个 Bokeh 图表，共享价格图的 `x_range`，并提供联动十字光标、悬停提示、图例，以及根据可见范围自动调整纵轴的 JavaScript 回调。日期时间用于标签，绘图坐标则使用连续的 K 线序号。[布局与坐标设置](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/_plotting.py#L198-L330)、[联动布局](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/_plotting.py#L638-L726)。

| 组成部分 | 实际表现形式 |
| --- | --- |
| 权益与收益率 | 曲线、历史权益高点相关阴影、峰值／期末值／最大回撤标注；可选插值和平滑 |
| 回撤 | 可选的独立曲线与最大回撤标记 |
| 逐笔交易盈亏 | 在出场时刻绘制收益率标记，大小对应交易数量绝对值，颜色表示盈亏，三角方向表示交易方向；连接入场与出场位置 |
| 价格与交易 | OHLC 蜡烛图；连接入场价格与出场价格的点状交易线段 |
| 指标 | 叠加在主图或放入独立副图，支持曲线和散点 |
| 成交量 | 有成交量数据时绘制独立的彩色柱状图 |

“盈亏气泡”可用于描述这种视觉形式，但该版本并非使用圆形气泡。[权益、回撤、盈亏与成交量实现](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/_plotting.py#L332-L473)、[价格、交易与指标渲染](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/_plotting.py#L518-L636)。

**事实：**`resample=True` 在超过名义上的 10,000 根蜡烛阈值后按日期时间聚合，也可以指定 pandas 频率。OHLCV 分别使用首值、最大值、最小值、末值与求和；权益取末值，回撤取最大值，指标通常取均值。交易按出场时间分桶，汇总数量和盈亏，按数量加权收益率，对时间取均值，并重新映射 K 线位置。`superimpose` 则单独负责叠加更大周期的蜡烛。这些操作发生在回测之后，仅改变展示数据。[重采样实现](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/_plotting.py#L113-L195)、[聚合规则](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/lib.py#L37-L73)、[大周期叠加](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/_plotting.py#L475-L516)。

**推论：**聚合后的交易图形不再对应精确的单次成交。Studio 可以借鉴联动视图和逐步展开细节的方式，但应保留原始成交标识，并明确告知用户发生了聚合，不能把展示聚合用作账务计算模型。

**事实：**上游选择 Bokeh 文件或 Notebook 输出，再调用 `show`，也可禁止自动打开浏览器。它生成的是独立交互文档，并非 Bokeh 服务端会话。独立 Bokeh 文档支持 JavaScript 交互，Python 回调则需要运行中的服务端。独立 HTML 也不必然意味着自包含或可离线使用：BokehJS 可以内嵌、从本地加载或使用 CDN。上游还添加了文档就绪后加载外部 iframe 的回调。[输出设置](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/backtesting/_plotting.py#L39-L99)、[Bokeh 嵌入方式](https://docs.bokeh.org/en/latest/docs/user_guide/output/embed.html)、[Bokeh 服务端](https://docs.bokeh.org/en/latest/docs/user_guide/server/server_introduction.html)。

**建议：**借鉴 Bokeh 的展示组织方式；代码编辑、文件保存与重新运行应由应用层承担。静态导出仍有价值，但没有执行宿主时，HTML 本身无法完成本地 Python 文件保存和回测重跑。

### 许可证边界

**事实：**上游 backtesting.py 使用 AGPLv3，Bokeh 使用 BSD-3-Clause，本仓库声明 Apache-2.0。Lightweight Charts 使用 Apache-2.0，并有 NOTICE 和署名要求。这些组件虽然共同参与图表流程，许可证仍各自独立。[固定版本的 backtesting.py 许可证](https://github.com/kernc/backtesting.py/blob/9c2b8e1c99f3a860883222ba8d6d5b5cac3a932d/LICENSE.md)、[Bokeh 许可证](https://github.com/bokeh/bokeh/blob/main/LICENSE.txt)、[OpenBacktesting 许可证](../../LICENSE)、[固定版本的 Lightweight Charts 许可证](https://github.com/tradingview/lightweight-charts/blob/b2ce010e4ad59f6556c9ed60e2b2b30feccdd2d1/LICENSE)。

**建议：**依据 OpenBacktesting 的公开数据契约实现 Studio 的数据映射，不应直接将 AGPLv3 的 backtesting.py 绘图源码复制进仅按 Apache 许可的组件。这一说明针对 backtesting.py；Lightweight Charts 则按下节用户约束纳入完整源码，并保留其许可证、NOTICE 和署名要求。本文不评估仓库历史代码的来源，也不提供许可证兼容性的法律意见。

## 3. Lightweight Charts 源码纳管与能力扩展

**用户约束：将最新稳定版 Lightweight Charts 的完整源码复制到本仓库，由我们构建和维护；现有 API 或扩展机制无法满足已确定的 Studio 功能时，直接修改图表库源码补齐。** 不能将“上游不支持”作为省略功能、降低精度或永久降级的理由。数据映射层仍有必要，但它不再是唯一允许修改的边界。

**事实：**本次研究查阅时，官方发布页标记为 Latest 的稳定版本是 **5.2.1**，提交为 [`b2ce010e4ad59f6556c9ed60e2b2b30feccdd2d1`](https://github.com/tradingview/lightweight-charts/tree/b2ce010e4ad59f6556c9ed60e2b2b30feccdd2d1)。这只是研究基线；实施复制时须重新核验官方最新稳定版本，并记录具体 tag、commit 和引入日期，不将本文版本号当作实施时仍然最新的保证。[版本发布页](https://github.com/tradingview/lightweight-charts/releases/tag/v5.2.1)。

**源码管理要求：**

- 完整源码放入拟议的 `studio/vendor/lightweight-charts/`，保留对应版本的源码、构建配置、测试、文档和许可证文件；不能只复制发布后的压缩 JavaScript 或挑选部分源码。
- Studio 前端必须使用仓库内这份源码的构建产物，确保本地修改实际生效，不能运行时又使用未经修改的 npm 或 CDN 版本。
- 保留上游来源、版本与提交记录，单独记录本地修改的目的和回归测试；后续上游更新通过可审查的版本升级合入，不能直接覆盖本地修改。
- 可复用现有 API 和图元扩展；遇到 API、渲染模型或交互能力限制时，由我们修改源码实现。补齐功能后验证图形语义、交互和性能，开发中的未实现提示不能作为功能验收通过的依据。

| 需求 | 已确认的库能力 | 对 Studio 的影响 |
| --- | --- | --- |
| 价格主图与指标／成交量副图 | 原生多面板，序列可以跨面板移动，支持面板尺寸与排序 API | 主要行情视图优先采用一个图表中的多个面板 |
| 独立权益图与行情图联动 | 订阅可见逻辑范围，以 API 设置和清除十字光标 | 统一时间与 K 线映射并防止循环触发；接口能力不足时修改本地图表库源码 |
| 交易标注 | `createSeriesMarkers`，支持相对 K 线或精确价格定位，以及 ID、文字和大小 | 使用真实成交 ID 与价格，重叠事件仅在展示层聚合 |
| 自定义区间填充、背景和交易连线 | 序列／面板图元与自定义序列 | 实现所需渲染；扩展机制不足时直接修改本地图表库源码 |

来源：[面板 API](https://tradingview.github.io/lightweight-charts/tutorials/how_to/panes)、[联动示例](https://tradingview.github.io/lightweight-charts/tutorials/how_to/set-crosshair-position)、[标记 API](https://tradingview.github.io/lightweight-charts/docs/api/functions/createSeriesMarkers)、[固定版本的标记类型](https://github.com/tradingview/lightweight-charts/blob/b2ce010e4ad59f6556c9ed60e2b2b30feccdd2d1/src/plugins/series-markers/types.ts)、[图元 API](https://tradingview.github.io/lightweight-charts/docs/plugins/series-primitives)。

**实现要求：**逐项支持现有完整绘图能力：蜡烛与逐根着色、曲线／阶梯线／柱状图／水平线、面板、数据有效性与就绪状态、缺口、偏移、区间填充、背景颜色、策略标记及实际成交。研究基线中的原生标记形状包括圆、方形和箭头，OpenBacktesting 还提供三角形；精确还原三角形、两条曲线之间的填充及背景绘制，可以通过自定义图元或修改图表库源码实现。上游能力差异应形成明确的实现任务，不能以“不支持”提示替代最终交付。[图表契约](../core/reference/plotting.md)、[固定版本的标记形状](https://github.com/tradingview/lightweight-charts/blob/b2ce010e4ad59f6556c9ed60e2b2b30feccdd2d1/src/plugins/series-markers/types.ts#L18-L21)。

**事实：**v5.1 引入可选的数据合并功能（data conflation），默认关闭，用于缩小时合并数据点。预计算通过增加初始耗时与内存来换取后续渲染速度；v5.2.1 改善了大序列中的标记悬停行为。官方没有承诺适用于所有场景的最大 K 线数量或延迟。[官方版本说明](https://tradingview.github.io/lightweight-charts/docs/release-notes)。

**推论：**渲染优化不会消除 JSON 传输、解析、数据重复或历史保留的成本。应从受控数据规模开始，测量有代表性的数据集，再按证据加入范围查询和展示数据视图。不能凭空宣称“支持数百万根 K 线”。

**事实：**Lightweight Charts 负责绘制传入的数据。数据获取、指标计算、应用控件、工具栏和持久化仍由应用负责。Advanced Charts 提供另一套 API 与现成的图表 UI，但 Advanced Charts 和 Trading Platform 都不包含 Pine Script 或 Strategy Tester。因此，TradingView 网站的 Strategy Report 是交互设计参考，并不是这些图表库提供的可嵌入回测引擎。[产品对比](https://tradingview.github.io/lightweight-charts/docs/product-comparison)、[Advanced Charts 不支持的功能](https://www.tradingview.com/charting-library-docs/latest/resources/Frequently-Asked-Questions/#unsupported-features)。

**事实与建议：**保留库的许可证和 NOTICE，在 Studio 及导出的查看器中提供 TradingView 署名与链接。官方入门文档明确要求署名。本地应用应打包所需静态资源；图表 Logo 本身不能替代所有分发声明。[署名要求](https://tradingview.github.io/lightweight-charts/docs#license-and-attribution)、[固定版本的 NOTICE](https://github.com/tradingview/lightweight-charts/blob/b2ce010e4ad59f6556c9ed60e2b2b30feccdd2d1/NOTICE)。

## 4. UI 设计约束与 TradingView 参考

**用户约束：Studio 的整体 UI 设计必须参考 TradingView，基础组件必须使用 shadcn/ui，不允许以未经设计的浏览器默认 HTML 样式交付界面。** 这些要求适用于首版和后续功能，不属于可选技术建议。

| 设计范围 | 必须遵守的要求 |
| --- | --- |
| 整体布局与视觉层级 | 参考 TradingView 的图表工作区、紧凑工具栏、多面板组织、报告区域与设置界面；图表是主要工作区域，代码和回测结果有明确、可切换的区域 |
| 策略参数与回测设置 | 参考 TradingView 的设置交互，采用清晰的分组、对齐的字段、提示、启用状态和应用操作，并保持策略参数与回测属性的区分 |
| 基础组件 | 按钮、输入框、选择器、复选框、开关、标签页、对话框、菜单、提示和表格等统一基于 shadcn/ui 组合或扩展 |
| 样式一致性 | 统一颜色、字体、间距、边框、圆角、控件密度及悬停、聚焦、禁用、错误等状态；图表、编辑器与基础组件的主题协调一致 |
| 原生 HTML 的使用边界 | 可以使用语义化 HTML 作为底层结构，但不能直接将浏览器默认样式的按钮、表单、选择器或表格作为成品 UI；自定义复合控件也必须纳入同一设计体系 |

**建议：**以 shadcn/ui 作为基础组件实现，以 TradingView 作为布局、信息密度和交互的设计参考；需要针对 Studio 调整主题和组件组合，不能把未经调整的默认组件拼装当作完成设计。Lightweight Charts 负责图表，Monaco 等编辑器负责代码编辑，其外围工具栏、弹窗和表单仍遵守上述组件与样式约束。

**事实：**当前官方文档将结果区域称为 **Strategy Report（策略报告）**。它结合了概要指标与权益、深入的绩效和交易分析，以及详细交易列表，涵盖总盈亏、回撤、盈利交易、利润因子、买入并持有对照、分布、连续盈亏、时间规律，以及持仓期间的有利和不利价格波动。这比旧截图中仅有概览与绩效汇总标签页的范围更广。[当前策略报告指南](https://www.tradingview.com/support/solutions/43000764138-tradingview-strategy-report-how-to-start/)。

**建议：**采用其信息层级：少量能体现指标状态的概要卡片、价格与成交图、权益与回撤、可点击定位的交易列表、配置与来源记录。根据现有 Portfolio 字段目录逐步加入其他分析。标签相同不代表计算公式、佣金处理、成交假设或交易拆分口径相同；应保留 OpenBacktesting 自己的计算方法标识。

**事实：**Pine inputs 会生成有类型约束的控件，支持分组、同行排列和提示信息；修改参数后会重新计算完整脚本。`active` 控制是否可编辑。特别需要注意，`display=none` 只影响状态栏和数据窗口中的展示，**不会隐藏 Inputs 控件**。策略参数 Inputs 与执行属性 Properties 也是两个概念。[Inputs 文档](https://www.tradingview.com/pine-script-docs/concepts/inputs/)、[策略属性](https://www.tradingview.com/pine-script-docs/concepts/strategies/)。

**建议：**分别提供**策略参数**、**回测设置**和**数据**区域。基于 `runtime.describe` 生成表单，保留声明顺序、分组、选项、提示和启用依赖关系。即使布尔与颜色参数默认 `display=none`，也必须能在表单中编辑。前端和框架均校验参数，以框架校验为准。Python 回测宜使用明确的**运行**或**应用并运行**操作，让用户一次调整多个参数后统一执行；不要每次按键都运行，也不要自动改写源码默认值。

## 5. 推荐架构

### 职责与打包

**已确认的方向：**初期在当前仓库采用轻量 monorepo，维护框架和 Studio 两个独立分发包，同时分离导入与构建边界。Studio 使用拟议包名 `openbacktesting-studio`，依赖兼容版本的 `openbacktesting`；该名称不表示软件包已经发布。后续可增加 `openbacktesting[studio]` 便捷安装入口，但核心框架运行时不能反向依赖 Studio。

| 层次 | 负责的内容 | 不应负责的内容 |
| --- | --- | --- |
| 框架 | 执行语义、参数与设置校验、账务计算、指标定义、不可变的公开导出 | HTTP、浏览器文件操作、编辑器状态、图表库类型 |
| Studio 宿主服务 | 工作区访问、源码快照、数据配置、工作进程、运行存储、展示数据视图、HTTP 生命周期 | 另一套盈亏计算或经纪商行为 |
| 浏览器应用 | 编辑器、表单、报告、导航、图表数据映射，以及纳入仓库的 Lightweight Charts 源码构建与扩展 | Python 执行、作为最终依据的交易与指标计算 |

前端基础组件采用 **shadcn/ui**，这是已确定的用户约束。推荐围绕它采用 React／TypeScript 与 Vite，配合本地 FastAPI 服务、Lightweight Charts 和 Monaco；这些实现选择不应进入核心框架的数据契约或基础依赖。Studio 分发包应包含已构建的 Web 静态资源，让最终用户只需 Python 和浏览器，无须 Node。Monaco 适合以代码为中心的界面；如果包体积和 Web Worker 配置成本超过收益，也可使用更轻的编辑器。完整的 Python 语言服务属于单独能力，嵌入编辑器并不自动获得它。

### 轻量 monorepo 的目录与工程边界

**建议：**保留框架现有目录，在 `studio/` 下增加独立的 Python 包与前端工程。以下是目标结构，尚未实施目录迁移或创建 Studio 工程：

```text
openbacktesting/
├── pyproject.toml          # 框架包配置
├── src/openbacktesting/   # 框架源码，保留现有位置
├── tests/                 # 框架测试
├── studio/
│   ├── pyproject.toml      # Studio Python 包配置
│   ├── src/               # 本地服务与启动入口
│   ├── web/               # 前端源码与构建配置
│   ├── vendor/
│   │   └── lightweight-charts/ # 上游完整源码及本地修改
│   └── tests/             # Studio 测试
└── docs/                  # 共享文档
```

| 工程边界 | 要求 |
| --- | --- |
| 依赖单向 | Studio 只调用框架公开接口，不依赖私有实现；框架不导入 Studio，也不引入其 Web 依赖 |
| 构建独立 | 分别生成框架和 Studio 的安装包，前端构建产物仅归入 Studio；显式限定各自的打包范围 |
| 验证独立 | 框架测试不需要前端工具链；Studio 单独进行前端、集成和安装验证，并验证实际安装包之间的版本兼容性 |
| 变更协同 | 需要同时调整公开契约、适配层和验证样例时，可在同一个 PR 中完成；发布仍须声明兼容版本，不能依赖本地源码路径掩盖缺失依赖 |

初期无需引入 Nx、Turborepo，也不必将框架搬到 `packages/`。先建立清晰的包边界，再根据实际构建规模决定是否增加工作区编排工具。同仓会增加前端工具链和 CI 配置，但首版接口仍需共同验证时，可减少跨仓变更与版本发布的协调成本。等 Studio 有独立维护团队、明显不同的发布节奏，并且公开契约稳定后，再评估拆仓。

### 安装方式与体积控制

**已确认的方案：同仓开发、独立分发、按需安装，Studio 内置构建后的前端资源。** 仅安装框架的用户不下载 Studio 的前端资源，也不安装其 Web 服务依赖。Studio 通过包依赖声明安装兼容版本的框架，不在自己的分发包中复制框架代码。

拟议安装方式如下；`openbacktesting-studio` 尚未发布，以下命令描述目标体验：

```bash
# 仅安装框架
pip install openbacktesting

# 安装 Studio，并自动安装兼容的框架版本
pip install openbacktesting-studio
```

| 分发内容 | 安装与运行边界 |
| --- | --- |
| 本地 Python 服务与启动入口 | 启动本地服务，在用户已有的浏览器中打开 Studio；必要的 Python 依赖通过包元数据声明 |
| 构建后的前端静态资源 | 包含 HTML、JavaScript、CSS、图标及图表、编辑器所需的运行资源，随 Studio 包发布；图表资源由仓库内的 Lightweight Charts 源码构建 |
| 开发工具链 | Node.js 和 `node_modules` 只用于开发与构建，不随运行包分发，用户无须安装 |
| 浏览器与桌面运行时 | 不打包浏览器或 Electron，复用用户已有浏览器 |

界面资源安装后即可在本地使用，启动时不再下载前端，也不依赖 CDN 加载必需资源。离线能力以本地界面和已具备的数据为范围；需要外部网络的数据源仍受其自身条件限制。

Lightweight Charts 的完整源码保留在开发仓库；面向最终用户的 Studio wheel 只携带所需构建产物及许可证、NOTICE 等分发文件，无须把上游开发文档、测试和构建工具链一并装入运行环境。源码纳管与用户安装体积分别管理。

**体积判断：**目前没有 Studio 构建产物，不能给出可信的安装大小。Monaco 等前端资源会增加下载和磁盘占用，首个原型应分别测量分发包大小、包含依赖的安装体积，以及首屏资源加载量，再决定是否需要更轻的编辑器。按需加载可减少首次打开时的资源加载量，但不会缩小已经打进安装包的资源总量。

### 公开结果与已保存运行的身份

**建议：**在现有 Portfolio 和 PlottingResult 外增加精简的 Studio 运行元数据，避免再造一套竞争性的统一结果模型。保留原始导出与 schema 版本，所有展示数据视图都应能追溯到原始结果。

运行元数据应记录：运行 ID 与状态；精确的源码内容、哈希与入口；本地依赖身份；输入 schema 哈希、请求及解析后的参数快照；实际生效的回测设置；数据集身份或指纹，以及请求范围与实际执行范围；周期、时区与交易品种假设；框架、Python 与依赖版本；可用产物和诊断信息。仅有文件路径无法确定实际执行了哪份代码。哈希能标识内容，却不能保存内容：要重新运行，仍需保留源码、依赖和数据，或提供可靠的不可变引用。任意策略都可能读取外部文件、网络、时钟或随机数，因此应记录复现限制，不能承诺所有策略都可完全复现。

现有优化器的 `ExecutionIdentity` 已区分策略与依赖哈希，恢复实验时也会核对数据、设置与环境身份。应沿用这些术语和语义，但不导入其私有辅助函数，也不假设优化器的 SQLite 结构就是通用 Studio 运行存储。优化运行有意关闭图表和日志历史，因此能打开旧试验报告不代表已经保存了对应图表。要重新生成图表，需要匹配的参数、源码、数据和设置，并生成与原试验关联的新运行。[优化器契约](../core/reference/optimizer.md)。

纯框架用户也必须能导出相同报告与图表数据，随后导入查看器。缺少图表、源码、日志或来源信息时，应明确减少可用操作，仍允许读取有效的 Portfolio 报告。

### 文件编辑与可复现的参数覆盖

**建议：**磁盘上的 `.py` 文件是源码的权威版本；UI 参数覆盖则是独立、绑定 schema 的运行配置。参数预设可保存在本地，无须修改 Python 声明。“将当前参数写回源码默认值”应作为后续独立操作，因为保留 Python 语法结构的编辑、枚举和导入处理属于另一类工作。

打开文件时记录内容版本或哈希，保存前再次比较。通过同目录临时文件和原子替换写入。外部编辑器修改文件后，若浏览器没有未保存修改，可重新加载；若有未保存修改，则保留双方版本，提供差异查看和冲突处理。文件监听能改善响应速度，但不能替代保存时的版本核对。冲突保存不能静默覆盖已有修改。

**保存并运行**应保存用户确认的编辑内容，捕获该版本，从同一版本重新发现 schema，校验请求，再执行。工作进程运行期间不得悄然换成另一份源码。源码或声明变化后，应标明先前报告不再对应当前编辑器内容，同时以原运行 ID 保留旧报告。拒绝过期的输入 schema 哈希，并明确处理预设的兼容问题，不能把旧值静默套到新标题上。[现有 schema 拒绝语义](../core/reference/inputs.md)。

### 执行宿主与本地服务边界

**建议：**在新建的工作进程中导入、读取描述并执行策略，使用选定的项目解释器、明确的工作目录和参数列表，而不是拼接 shell 命令。新进程可以避免旧 Python 导入和全局状态污染重跑，也允许终止卡住的策略而不关闭 UI 服务。Python 提供子进程生命周期与进程组／会话控制，但仍需明确处理不同操作系统的终止行为。[Python 子进程文档](https://docs.python.org/3.14/library/subprocess.html)。

使用运行 ID，以及明确的排队、运行中、成功、失败、已取消状态。完成的产物原子持久化；失败和取消时保留有容量限制的诊断信息，不得伪装成成功报告。忽略已取消或已被替代运行的迟到事件。stdout／stderr 应与结构化结果通道分开。停止操作应在可支持时先请求取消，宽限期后终止工作进程及其子进程。现有优化器的取消会等待正在运行的候选项完成，不是单次回测的即时中断接口。[优化器取消行为](../core/reference/optimizer.md)。

进程隔离**不等于沙箱**：Python 代码仍拥有当前用户的文件和网络权限。服务默认绑定本机回环地址，校验 Host／Origin，对需要权限的 API 要求每次启动生成的会话令牌，解析真实路径后将文件操作限制在选定工作区内，并避免向远程来源开放 CORS。这些约束直接来自“通过 HTTP 暴露本地文件写入与任意 Python 执行”的组合；仅使用 localhost 并不等于完成授权。远程和多用户执行不应纳入首版。

宿主还需要最小的**数据配置**：明确的本地来源或加载器、交易品种、周期、时区、品种规则和选择的时间范围。宿主先加载实际 DataFrame 并记录数据身份，再调用 `runtime.run`。初期使用明确的本地数据集和适配器即可，无须先建设完整的数据市场或通用数据供应商平台。[运行时必需的数据参数](../core/reference/runtime.md)。

## 6. 渲染正确性的不变量

### 时间、K 线、事件与缺失值

**事实：**PlottingResult 将带时区的时间轴导出为纳秒字符串，并另行区分无时区日期时间轴和序号轴；Portfolio 时间戳同样保留类型信息。Lightweight Charts 日内时间类型 `UTCTimestamp` 使用**秒**，其序列 API 要求数据按时间排序。OpenBacktesting 时间参数使用**毫秒**。这三种单位不能混用。[图表编码](../../src/openbacktesting/plotting/encoding.py)、[Portfolio 编码](../../src/openbacktesting/portfolio/models.py)、[LWC 时间戳单位](https://tradingview.github.io/lightweight-charts/docs/api/type-aliases/UTCTimestamp)、[固定版本的序列 API](https://github.com/tradingview/lightweight-charts/blob/b2ce010e4ad59f6556c9ed60e2b2b30feccdd2d1/src/api/iseries-api.ts#L144-L190)、[参数单位](../core/reference/inputs.md)。

**建议：**

- 在渲染器之外保留精确纳秒和 K 线 ID，不要把纳秒直接转成 JavaScript Number。为图表显式转换，并检测不同原始时刻转换后变成同一时间戳的情况。不要给序号轴编造日期，也不要猜测无时区数据的时区；应提供明确的轴适配方式，或说明限制。
- 使用标准 UTC 坐标，按选定时区格式化展示标签。Lightweight Charts 没有原生时区模型；平移底层时间戳可能在夏令时切换附近改变排序和身份。展示时区只影响呈现；修改框架 `DataContext` 的时区则可能改变策略日历与统计聚合，需要重新运行。[图表库的时区限制](https://tradingview.github.io/lightweight-charts/docs/time-zones)、[数据上下文](../core/reference/data.md)。
- 保留 `valid`、`ready`、缺失状态、`gap_policy` 和展示偏移。尚未就绪的指标点不能当作零。保留 `anchorBar` 和 `knownAtBar`：将已确认事件画在较早的 K 线上，不代表当时已经知道该事件。策略标注与实际成交必须保持区别。[图表语义](../core/reference/plotting.md)。

**关键仓库事实：**`series.account` 包含标记为 `ordered=False` 的合成 `bar_range` 极值，以及执行、K 线和终止时刻的观测。`series.close` 保留每根普通 K 线的收盘观测和独立终止快照，后者可能与最后一根 K 线共享时间戳。将全部账户行按顺序连线会虚构盘中价格路径；将全部收盘行直接传给“每个时间点一个值”的图表序列，则会产生重复时间问题。[账户观测构建](../../src/openbacktesting/portfolio/builder.py#L72)、[收盘观测选择](../../src/openbacktesting/portfolio/builder.py#L112)、[导出的时间序列](../../src/openbacktesting/portfolio/builder.py#L337)。

**建议：**默认权益曲线使用 `series.close`；对最后一个图表点，明确选择终止值，并在详情中保留两份观测，或使用单独的终止标注。无序的盘中上下界应画成范围，不得虚构先后顺序。回撤指标与仅基于收盘的曲线可能采用不同路径，应标明计算方法并提供相关区间信息，不能依据渲染后的曲线重新计算指标。

### 展示降采样与回测计算

**建议：**图表缩放和聚合不得重新执行策略或改变汇总统计。改变回测周期需要新运行；展示降采样只是原运行的另一种视图。完整精度的事实与稳定 ID 必须保留。

对较大结果，先读取概要，再分页获取交易和事实，仅请求需要的图表序列及范围。OHLCV 按明确定义的分桶边界聚合；权益和回撤使用末值或保留极值的表示方式。指标线需要明确的展示策略，随意取均值可能掩盖交叉。密集成交可聚合显示数量和详情，但必须保留底层精确 ID，不能将聚合均价显示为真实成交价。LWC 的数据合并应在这些传输与语义边界确定后使用。

一次本地探索性运行使用 120 根 K 线，未压缩的普通 JSON 中，图表约 133 kB，Portfolio 约 791 kB。这是示例观察，不是性能基准或容量承诺；它说明不宜默认在每次交互时发送完整账户和事实结构。该探测使用本文仓库基线下已有的绘图示例与公开导出函数。

### 指标与部分结果的准确呈现

**事实：**Portfolio 指标携带 `value`、`unit`、`methodId`、`status`、`reason`、`sampleCount` 和 `reference`，未定义值转换为 JSON null。报告还记录终止信息，成功导出并不证明已处理请求范围内的每根 K 线。[指标表示方式](../../src/openbacktesting/portfolio/models.py)、[Portfolio 契约](../core/reference/portfolio.md)。

**建议：**不可用指标显示为“—”并说明原因，不得显示为零；根据字段目录处理单位与计算方法标识，区分小数比例和百分点数值。无交易、只有未平仓持仓、历史过短、提前终止或关闭图表采集的结果，都应仍可使用。缺少图表不应影响有效报告的读取；未完成整个区间的运行不能标成完整区间回测。不要为了凑齐熟悉的 TradingView 布局而编造不支持的指标。

## 7. 最小可用交付与验证

**建议：**首版完成一条完整流程：选择本地策略与数据配置；编辑和保存，并检测冲突；生成有类型约束的参数与设置表单；在独立工作进程中保存并运行；查看概要、权益与回撤、联动的价格主图和指标副图、实际成交；无需执行代码即可重新打开已保存结果。流程中应准确处理无数据、失败、取消和指标缺失状态。多次运行对比、优化器 UI、实时行情、大量绘图工具和 Python 语言服务集成可后置。

正式确定渲染方案前，应使用有代表性的现有 PlottingResult／Portfolio 数据样例，验证同一根 K 线多次成交、终止快照时间重复、无序账户极值、标记确认时机、数据缺口与就绪状态、所有现有图形类型、夏令时和亚秒时间轴、过期 schema，以及无交易结果。应在目标浏览器中测量有代表性的 K 线、指标与事件规模；本研究尚未确定容量目标。

**UI 验收约束：**首版即应检查图表工作区、参数设置、编辑器区域和结果报告是否体现 TradingView 的设计参考；基础控件是否统一使用 shadcn/ui；是否存在未经设计的原生 HTML 默认样式。正常、加载、空数据、错误、禁用和键盘聚焦状态都必须遵守同一套设计规范，不能以“功能已通”为由推迟这些要求。

**安装验收：**分别在干净的 Python 环境中验证框架与 Studio 的安装包：框架安装不引入 Studio 资源和依赖；Studio 在没有 Node.js 的环境中可启动，并从本地加载完整界面资源。记录分发包大小、依赖安装体积和首屏加载量，不以开发服务器运行成功替代安装包验证。

**图表源码验收：**核对完整源码的上游来源、固定版本、构建路径和分发声明；确认 Studio 使用本地源码的产物。对每项补齐能力保留回归用例，并运行相关上游测试，不能以“上游没有此功能”为由跳过已确定的图表需求。

研究期间运行了 5 项现有针对性测试，均通过，覆盖仅声明阶段的策略发现、源码重载后拒绝过期请求、冻结的图表导出、执行事实隔离，以及严格的时间与数值编码。这验证的是现有接口基础，**不代表 Studio 已经实现**。源码与官方库文档支持方案的可行性；渲染保真度与性能仍需要浏览器适配原型验证。
