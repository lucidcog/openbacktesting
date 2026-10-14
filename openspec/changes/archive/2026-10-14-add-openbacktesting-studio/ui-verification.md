# Studio UI 回归验证记录

## 验证边界

本记录区分组件交互测试和真实浏览器验证。本轮已按下方控件清单完成验收：前端 291 项、Studio 后端 86 项测试通过，配合真实 Chrome 工作流和安装包验证；结论依据控件映射，不以测试数量代替覆盖证明。组件测试使用模拟 API；App 组件测试模拟图表、编辑器和可调整面板的布局边界，真实画布、Monaco 和拖拽另有下文的浏览器证据。

## 已覆盖的组件交互

| 范围 | 测试标识 | 核心不变量 |
| --- | --- | --- |
| 历史结果 | UI-A01–A04、UI-A08 | 重复选择不取消唯一读取；旧响应不覆盖新选择；失败日志不污染成功结果 |
| 文件与布局入口 | UI-A05–A07、UI-A10–A11 | 搜索、清空、主题、侧栏、页签和图层的状态变化正确 |
| 保存与执行 | UI-A12–A17 | 草稿保留；保存冲突阻止运行；首次确认只提交一次；普通设置不执行 |
| 目录浏览 | UI-W01–W06 | 上下级导航、路径提交、取消、错误恢复和过期响应隔离 |
| 目录集成 | UI-W07–W14 | 首次不扫描；先恢复目录再读文件；失效路径不回退扫描；仅成功选择持久化；草稿与活动运行阻止切换 |
| 报告 | UI-R01–R09 | 方向与表格切换、分页、详情定位、过期响应隔离、错误与重试 |
| 日志 | UI-L01–L04 | 使用正确运行快照；切换或关闭后旧读取不重新打开；失败可重试 |
| 参数与回测设置 | UI-P01–P10、UI-S01–S02 | 控件值类型、步进、条件禁用、错误关联、时间边界和全部设置字段 |

具体断言在 `studio/web/src/**/*.interactions.test.tsx`。已有纯函数测试继续覆盖协议、图表模型、布局、输入和报告计算约定。

## 导入导出、外部文件变更与快照重跑

- UI-X01–X06 共 14 个用例，覆盖导出选项的全部 8 种组合、取消／失败反馈、JSON 与归档导入、重复选择失败文件、快照重跑和只读界面边界。新增 8 项归档测试核对各组合实际包含的文件，原始结果不变。
- UI-E06–E12 覆盖外部文件自动刷新、冲突两种处理路径、删除／恢复、保存与轮询竞争以及连续保存快捷键。修复前断言证明 Save 在删除后仍可点击，且过期轮询响应会回退刚保存的版本。现按读取开始时的磁盘版本隔离旧响应，冲突禁止保存，恢复原版本后解除冲突。
- UI-M01–M05 检查 Monaco 集成的最新保存回调、空草稿、快照只读／行定位、只读差异对照和文件／主题更新；这些测试模拟 Monaco 边界，不代替下面的真实编辑器验证。
- Chrome 实际默认导出包含 6 个归档成员，没有源码、数据或日志；全选导出包含 38 个成员，其中源码 17 项、数据 12 项，以及 logs/stdout/stderr。浏览器下载事件监听曾超时，后续直接检查已落盘的归档确认成功，没有把超时当作下载失败。
- 重新导入默认归档生成 `2fdc5be50a`，图表和 249.66% 报告正常；导入独立 JSON 生成 `dbe01f2f10`，显示 0.97% 报告，同时明确告知缺少图表数据。历史快照重跑生成 `c0951aff02`，结果仍为 249.66%。
- 无效 JSON 浏览器验证发现错误响应展开整个 schema（约 30 万字符），顶层 null／数组／数字／字符串另会触发 500。现统一为简短的 422 校验反馈；新增 5 项接口测试证明错误长度受控且失败不新增运行记录。
- 使用独立临时文件 `qa_ui_editor.py` 验证真实 Monaco 粘贴与 Cmd+S，并核对磁盘内容；再分别验证保留草稿保存、放弃草稿重载、文件移走后的写入禁用、恢复文件后的保存。测试文件已移出工作区保留在 `/tmp/studio-ui-editor-recoverable.py`，原策略源码未修改。
- 前端完整 17 个测试文件、211 项测试通过；Studio 后端完整 85 项测试通过；typecheck、lint、构建和 Python 格式检查通过。
- 截图证据：`/tmp/studio-imported-verified.jpg`、`/tmp/studio-file-conflict-verified.jpg`、`/tmp/studio-file-deleted-verified.jpg`。

## 数据与文件并发专项证据

- 新增 `DataForm.interactions.test.tsx` 的 UI-D01–D13，共 43 个用例，覆盖三种来源、三种样例、CSV 映射、时间编码、周期、标的字段、可空值、数字草稿与 JSON 校验。
- UI-E01–E05 覆盖慢文件读取、重复读取合并、保存期间继续编辑、并发忙碌状态和过期读取失败；旧响应不得抢回编辑器焦点或覆盖新草稿。
- UI-C01–C08 覆盖预设保存／加载／Defaults、无效数据阻止保存与应用、数据配置保存、保存失败、源码范围传递及切换页签保留无效 JSON。
- 修复前，数据表单 9 项断言失败；慢文件覆盖与重复读取 2 项断言失败；跨页签 JSON 草稿保留断言失败。修复后前端全部 16 个测试文件、184 项测试通过，typecheck、lint 和构建通过。
- 浏览器验证发现 Save profile 和 Save preset 的 HTTP 接口均错误地把 `payload` 当作查询参数，返回 422。原因是延迟求值的类型注解引用了函数局部导入的模型。模型改为模块级导入后，新增的两项真实 HTTP 保存／读取／非法版本校验回归测试通过；Studio 后端完整 72 项测试通过。
- Chrome 实测：输入 `0.` 保持草稿，清空 Minimum notional 后 Save profile 和 Apply 均禁用；无效 JSON 在 Data → Source → Data 切换后保持原文并阻止保存。逐项编辑了 CSV 路径、时间列、五个 OHLCV 映射、时区、标的、周期倍数、起止时间、价格步长、最小数量、最小金额和币种。
- 修复接口并重启后，浏览器创建测试配置 `qa-ui-data`、预设 `qa-ui-preset`；修改表单后重新加载，Symbol 恢复为 `QA-SAVED`，Cash 恢复为 `12345`，Defaults 恢复 `10000`。已核对工作区 `.openbacktesting/studio/` 中保存的 JSON。测试配置保留在本地，没有修改策略源码。
- 截图证据：`/tmp/studio-data-invalid-verified.jpg`、`/tmp/studio-preset-restored-verified.jpg`。

## 目录选择专项证据

- 前端全部 15 个测试文件、128 项测试通过；typecheck、lint 通过。
- `studio/tests/test_host.py` 与 `studio/tests/test_cli.py` 共 12 项测试通过，验证惰性工作区选择、目录隔离、旧身份请求拒绝和 CLI 行为。
- 在用户当前 Chrome 配置中新建 Studio 标签页验证：打开目录选择器、进入父目录、重新选择 `examples/strategies`、打开并刷新；侧栏仅显示该目录的 17 个策略文件。
- 成功 Run `a8633dc054` 的报告显示 249.66%；再次点击该记录后仍显示报告，Loading 数量为 0。
- 截图证据：`/tmp/studio-workspace-picker-final.jpg` 与 `/tmp/studio-workspace-restored-final.jpg`。临时截图不属于仓库交付文件。

## 图表窗口、事件与配置迁移专项证据

- UI-G01–G12 覆盖 Earlier／Later／All bars、独立报告与图表重试、过期窗口响应、成交选择、聚合成员分页／重试、价格／时间拾取及取消。UI-C09–C10 验证不兼容预设取消不改变设置，确认迁移才应用保留值和回测属性。
- UI-R10–R11 验证分配记录定位使用独立的 `fillBars` 元数据，不修改原始记录；缺少有效 bar 时只展示详情，不发出 NaN 区间请求。后端新增对应元数据测试，完整 86 项测试通过。
- 新增 `MarketChart.interactions.test.tsx`，UI-G13–G19 验证副图与成交量独立、完整范围允许足够小的 K 线间距、销毁时解除订阅、异步范围通知不循环、后加载净值图恢复主图范围、聚合桶内部样本可打开成员，以及图层开关控制聚合标记。
- 真实浏览器曾发现 All bars 被异步图表联动覆盖，最终停在末尾约 1,200 根；仅调整间距不能解决。现只有用户手势发起新的范围联动，程序设置的延迟通知不再次发布；显式窗口切换取消未执行的缩放请求。
- 浏览器还发现成交量先创建时，图表库只追加一个缺失 pane，造成后续策略副图落到成交量 pane。现提前创建所有 pane，验证主图、策略副图、成交量分别显示。
- 使用真实核心引擎生成 12,345 根分钟 K 线的合成验证快照，标的为 `QA-SYNTH`，归档 provenance 明确标为 synthetic。导入记录 `3a4903860d` 用于分页、全量区间和聚合事件验证；不把该数据当作实际投资结果。
- Chrome 实测完整区间为 `1–12345 / 12345 · aggregated ×15`；点击 bar 2445 显示所在桶的 1 笔成交与 15 个信号，Locate original fill 定位到 bar 2450 的 `fill-48`，主图成交高亮与净值图同步。截图：`/tmp/studio-chart-fill-verified.jpg`。
- 再次打开手动目录选择器确认当前目录与取消行为；截图：`/tmp/studio-workspace-manual-final.jpg`。
- 前端完整 18 个测试文件、239 项测试通过，lint 和包含 typecheck 的生产构建通过。图表集成测试模拟 Lightweight Charts API；真实画布证据单独记录，不以模拟测试替代浏览器验收。

## 参数、运行生命周期与布局收尾验收

- UI-P11–P12 对齐核心 Session 校验：拒绝超出 0000–2359 的时钟、重复星期；规范化默认星期、跨夜区间和 `24x7`。UI-S03–S06 覆盖执行属性的有限数值、上下界、费率类型与数量类型配对，以及 `0.` 草稿跨页签保留。非法 Properties 阻止 Apply、保存预设和 Run。
- Chrome 实测修改全部数值属性、三个布尔开关和五类枚举；切换费用／数量类型会重置配对值，空 Cash 禁用保存与应用。Session 的重复星期显示字段错误。截图：`/tmp/studio-properties-verified.jpg`。
- 临时策略 `qa_ui_lifecycle.py` 以 slow 模式生成 `8debb332f2`，点击取消后状态落盘为 cancelled；fail 模式生成 `93b751d0ab`，保存明确的异常与源码行号。点击 Snapshot 打开第 16 行，原文件移走后仍可读取旧源码，向只读 Monaco 粘贴文本未改变内容。
- UI-A18–A21 补充各运行状态的身份隔离、取消失败重试及选中运行完成后的自动加载。原实现点击失败记录只替换日志，顶部和重跑仍指向上一成功 Run；现日志、标题、历史选中项与重跑使用同一 ID，失败记录明确显示没有完成的图表。截图：`/tmp/studio-failed-run-identity.jpg`、`/tmp/studio-failure-source-verified.jpg`。
- 实测将 QA length 的上限从 20 改为 10：17 被识别为不兼容值；Cancel 不应用迁移；Review inputs 恢复默认 5；加载旧预设再次提示超出 Maximum 10。真实画布一次点击同时更新同一 inline 组的价格和 UTC 时间，Cancel pick 保留拾取前值。
- UI-A20 验证拖拽比例持久化，折叠产生的单面板通知不能覆盖两面板比例。Chrome 拖至 44.321%，折叠／展开、刷新后仍为 44.321%；结束时恢复原约 61.994% 布局。
- UI-G21–G24 验证缩放防抖、显式窗口操作和切换 Run 取消旧任务、主题／图层变化保留视区与 pane 比例。Chrome 滚轮缩放和平移后，主图与净值图定位到相同日期；拖拽成交量 pane 后，切换主题与图层保持高度。
- 独立执行 `studio view` 导入 portfolio JSON。实测 Overview、Performance、方向切换对应组件用例；七种明细、Previous／Next、Details、Settings & Data、Logs 可用。页面没有 Run、Import、保存源码或选择目录入口，缺少图表时图层开关禁用，页脚明确只读。截图：`/tmp/studio-readonly-verified.jpg`。
- 最后在成功记录之间切换并重复点击当前记录，报告仍显示 249.66%，Loading result 数量为 0。截图：`/tmp/studio-ui-audit-final.jpg`。
- 临时策略已移至 `/tmp/studio-ui-lifecycle-recoverable.py`；测试运行与 `qa-ui-migration` 预设保留在本地 `.openbacktesting/studio`。没有改写原策略示例。

## 当前可交互控件的完成审计

| 控件／操作 | 自动化证据 | 真实工作流证据 |
| --- | --- | --- |
| 侧栏开关、主题、底部折叠／展开、布局拖拽与恢复 | UI-A06、A20、layout.test.ts、UI-G24 | Chrome 切换、拖拽、刷新，比例恢复 |
| 目录选择、路径浏览、上下级、取消、失效路径恢复 | UI-W01–W14；host／CLI 测试 | 选择 examples/strategies，仅显示目录文件，重启恢复 |
| 文件搜索、清空、Escape、文件选择 | UI-A05、A12、UI-E01–E05 | 搜索并打开策略、切换后保留草稿 |
| 编辑、保存、Cmd+S、冲突审阅／重载／保留草稿、删除后恢复 | UI-A12–A17、UI-E06–E12、UI-M01–M05 | 真实 Monaco、磁盘内容核对与外部变更 |
| Run、首次确认、Apply & Run、取消、快照重跑 | UI-A09、A14–A19、A21、UI-X05、workflow.test.ts | 成功运行、slow 取消、fail 异常、历史快照重跑 |
| 历史选择、重复点击、快速切换、失败／取消记录 | UI-A01–A04、A08、A18、A21 | 缓存报告显示、失败身份一致、重复点击无永久 Loading |
| 图层开关、全区间／前后窗口、视区缩放／平移、十字线 | UI-A10、UI-G01–G05、G13–G17、G19–G24、sync.test.ts | 12,345 根合成数据、完整范围、主副图和净值联动 |
| 图表选点、成交高亮／清除、事件成员分页／定位／重试 | UI-A11、UI-G06–G12、G18 | 聚合桶成员、fill-48 定位、价格时间成对拾取；分页及重试由组件测试覆盖 |
| Overview、Performance、All／Long／Short、指标可用性 | UI-A07、UI-R01、R08、report.test.ts | 成功快照与只读导入报告 |
| 七类明细表、分页、Details、原始精度和成交定位 | UI-R02–R07、R10–R11；reports 测试 | 七表逐项查看、121 条记录翻页、原始精度详情 |
| Settings & Data、Logs、源码快照打开／关闭／重试 | UI-R09、UI-L01–L04、UI-M03 | 失败第 16 行历史快照、只读粘贴验证、原文件移走后仍可读 |
| 九种输入、数值步进、条件禁用、帮助、错误关联、选点取消 | UI-P01–P12、UI-G10–G12、inputs.test.ts | 参数逐项编辑、条件禁用、Session 错误、真实画布拾取 |
| Properties 全字段、类型配对、空值、数值范围 | UI-S01–S06、settings.test.ts | 全数值、开关及枚举操作，非法字段禁用提交 |
| Data 来源／样例／CSV 映射／时间／标的／JSON、配置保存与加载 | UI-D01–D13、UI-C03–C06、C08；configuration 测试 | CSV 与 loader 表单编辑、无效 JSON 保留、配置保存并重载 |
| Source roots／resources、预设标识、保存／加载／Defaults、schema 迁移确认／取消 | UI-C01–C10、workflow.test.ts | 预设保存、Defaults、旧参数上限改变后的确认和取消 |
| 导入、导出、资源开关、下载、取消、错误关闭／重试 | UI-X01–X06、UI-A13、A17；8 组合归档测试 | 默认及全选下载、检查归档成员、JSON／归档导入及非法 JSON |
| 只读模式边界、无图表状态、外部图表署名链接 | UI-X06、UI-G20、UI-A22；CLI／host 测试 | 独立 viewer，无执行／编辑入口，状态说明正确 |

## 前阶段检查与可复现证据

- `npm --prefix studio/web test`：19 个文件、291 项通过，日志 `/tmp/studio-final-ui-tests.log`。
- `npm --prefix studio/web run lint` 通过；`npm --prefix studio/web run build` 包含 TypeScript 检查并验证 19 个本地资源。构建仍有大于 500 kB 的 chunk 提示，不影响当前功能验收。
- `studio/.venv/bin/python -m pytest studio/tests -q`：86 项通过，日志 `/tmp/studio-chart-backend-final.log`；有一条 Starlette/httpx 弃用提示。
- `uv build studio --out-dir studio/dist` 成功；wheel 46 个成员、1,267,280 字节，sdist 68 个成员、1,463,078 字节；分发边界检查通过。
- `studio/scripts/check_installation.py` 在仓库外分别安装最终 wheel／sdist，验证 core-only 回测、Studio 工作区、worker、离线只读查看器、本地静态资源和默认私密资源不导出。运行阶段禁止外连，PATH 无 Node。日志 `/tmp/studio-final-installation.log`。
- 测试方法边界：浏览器验证使用当前 Chrome 配置 Zale；组件测试控制网络失败、延迟和并发的精确顺序，导出全 8 种组合由归档测试逐项证明，浏览器走默认与全选路径。这里不声称所有浏览器／操作系统均已验收，也不声称未知缺陷不存在。当前产品控件清单没有留下未覆盖的操作项。

## 主副图绘制矩阵与结果区域切换补充验收

本次需求覆盖范围如下，测试 ID 使用 `UI-V` 表示绘图矩阵、`UI-DOCK` 表示布局，避免与参数／数据表单测试编号混淆。

| 要求 | 可重复的验证证据 |
| --- | --- |
| `line`、`step`、`histogram`、`level` 在主图和副图绘制 | `UI-V01` 的 8 个组合：目标 pane、独立价格轴、实际数据点、阶梯样式、柱状基线、水平线值和颜色 |
| 填充与背景色在两个面板绘制 | `UI-V03–V04` 的 4 个组合执行实际 `Bands` renderer，断言多边形坐标、颜色、整面板高度和清除后不绘制 |
| 四种 marker 形状 × 三种位置 × 两种面板 | `UI-V02` 的 24 个组合：marker 只附着到指定面板，保持原始 bar、形状、位置、价格、文字和颜色 |
| K 线着色、成交量 | `UI-V05`：OHLC 值和 body／wick／border 着色、清除覆盖、成交量独占副图；核心 `bar_color` 无 pane 参数，不能伪造副图 K 线能力 |
| 连续序列缺失与偏移 | `UI-V06` 的 6 个组合覆盖 line／step／histogram × 主副图，预热遮罩、缺失断线与显示偏移正确 |
| 核心导出与后端投影 | `studio/tests/test_plot_matrix.py` 用真实回测生成固定样本，逐类型检查 pane／scale、窗口数据、fill 和 marker 身份；样本与重新导出的内容必须完全一致 |
| 底部／右侧切换与持久化 | `UI-DOCK01–DOCK03`：按钮切换方向，保持图表和编辑器 DOM、草稿与标签页，不提交新回测；恢复位置和比例、折叠后展开、只读报告均覆盖 |

固定样本为 `studio/tests/fixtures/plotting-matrix.json`，可执行 `studio/.venv/bin/python studio/tests/test_plot_matrix.py` 重新生成。样本只用于绘制验证，不代表投资表现。导入浏览器的合成记录 ID 前缀为 `05f72bbb18`，包含 32 根 K 线。

真实 Chrome 验证已确认：右侧布局拖拽后比例为 51.062%，刷新后方向和比例不变；切到底部后纵向拖拽为 62.757%，键盘向上调整为 57.757%。测试使用实际 shadcn 可调整面板与 vendored 图表画布，补足 App 组件测试模拟布局和图表的边界。

此次真实样本导入发现并修复无时区时间编码差异：Plotting 使用 ISO 本地时间标签，Portfolio 使用纳秒整数字符串；校验先规范化后比较，仍拒绝相差 1 纳秒的错配。净值图同时恢复可读的无时区日期标签并保留十字线纳秒精度，见 `UI-V07` 和 `model.test.ts`。


## 日志、完整优化器与本轮最终验收

- 日志交互参考 TradingView 官方 [Pine Logs 说明](https://www.tradingview.com/support/solutions/43000710876-i-d-like-to-learn-more-about-pine-logs/)。保存后的日志提供时间、级别、来源、起始时间、大小写／完整词／正则搜索、分页及源码／bar 定位；不伪造实时采集开关。`UI-L01–L11` 和 `UI-LA01` 覆盖正常交互、无效正则、过滤、分页、空态、源码和定位。
- Chrome 中运行 `strategy_logs.py` 得到 `3f799fcd99`：1,869 条保存日志与截断提示可见，搜索 `bar=300,` 得到一条；定位加载原始 bar 201–401，未创建新 Run；源码入口打开快照第 20 行。截图：`/tmp/studio-logs-verified.png`。
- 优化器紧随 Code，公开九种输入类型、数值范围、约束、计划预览、显式执行、取消／续跑、所有核心结果字段、排序／过滤／分页、全部试验与完整 Portfolio。`UI-O01–O13`、`UI-OA01–OA02` 覆盖工作流、旧响应隔离、草稿保存、忙碌状态、导入导出和超过 100 项的字段检索。
- 真实 EMA 优化暴露 `PortfolioSnapshot.to_dict()` 派生的异常值边界仍包含 numpy 标量，导致核心优化持久化拒绝结果。修复为统一导出原生 JSON 类型，保留指标数值和方法；核心回归核对直接回测与保存试验的完整 Portfolio 一致。
- Chrome 实验 `c10af7f0`：Fast period 12–14 × Allow shorting false／true 共 6 个组合。先预览，再开始、取消、续跑，最终 6 项成功。字段目录有 1,749 项；按总盈亏降序并过滤 ≥800，返回 840.32 与 825.26。打开首条生成 `0c904a489f`，报告显示相同盈亏与 49 条已平仓记录；应用参数前的确认界面显示 Fast=12、Slow=26、数量=1、允许做空。
- 页面导出 `c10af7f0e39148c58d157887f90d2d29.sqlite` 后，通过文件选择器重新导入为 `4445e628`，6 条试验及指标完整恢复，导入实验不提供执行／续跑入口。核心优化目前保存 Portfolio，不收集逐试验图表与日志；打开报告明确显示缺少绘图数据，不隐式重跑策略。
- 实测底部／右侧切换、调整比例和折叠恢复。最终右侧布局同时展示主副图验证样本和导入实验，截图 `/tmp/studio-optimizer-import-right-verified.png`；排序过滤截图 `/tmp/studio-optimizer-ranked-verified.png`。右侧窄面板结果表允许横向滚动，操作列固定。
- 前端完整 **397 项**通过（22 个测试文件），日志 `/tmp/studio-final-ui-all.log`；Studio 后端完整 **135 项**通过，日志 `/tmp/studio-final-backend-all.log`。优化器后端 10 项覆盖九种参数、全部七种过滤运算、多排序、分页、失败继续、取消强制终止与续跑、源码篡改拒绝、互斥与只读边界。
- 核心 optimizer／Portfolio 相关回归 **99 项**通过；vendored 图表既有 **144 项**测试及类型检查通过。主副图矩阵由真实核心导出、投影、组件 renderer 和浏览器画布共同验证；真实 PriceScale 测试覆盖不同高度与正反转换，修复极矮副图标记边距导致价格轴反转。
- 生产构建通过，记录 19 个本地资源；wheel 51 个成员、1,286,289 字节，sdist 76 个成员、1,488,313 字节，分发检查通过。仓库外分别安装 wheel／sdist，禁用外连且 PATH 无 Node，验证 core-only、Studio worker、真实优化、查询与数据库备份、只读查看和默认分享边界。日志 `/tmp/studio-install-optimizer.log`。
- 验证范围为当前 macOS 和用户 Chrome Zale。网络失败、并发顺序、所有输入与筛选组合由自动化覆盖；浏览器走真实 EMA、日志和合成绘图路径，不声称全部系统／浏览器组合已验收。现存构建大 chunk 提示及 Starlette/httpx 弃用提示不影响本轮通过结果。
