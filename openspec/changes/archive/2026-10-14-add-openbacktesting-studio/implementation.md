# Studio 实施与验证记录

本变更在同一仓库提供独立安装的 Studio；核心包不增加 Web 依赖。133／133 项实施任务已完成；任务复选框与下列实际验证证据一起记录进度，不能把静态检查解释为浏览器验收。

## 能力追踪

下表路径均相对仓库根目录；相关源码、自动检查和文档在提交中一起维护。

| 能力 | 实现责任 | 检查入口与关键不变量 |
| --- | --- | --- |
| `package-identity` | `studio/pyproject.toml`、`scripts/check_package.py` | `tests/test_language_check.py`、`tests/test_package_identity.py`；两包导入根与依赖方向独立 |
| `repository-language-policy` | `scripts/check_language.py`、`scripts/language-exceptions.json` | `tests/test_language_check.py`；中文文档精确摘要登记，上游原文逐文件来源登记，本地新增不能借目录绕过 |
| `standalone-python-package` | 根包构建配置、`studio/hatch_build.py` | `studio/scripts/check_installation.py`；离开仓库安装核心并读取资源，不依赖 Studio 或 Node |
| `studio-distribution` | `studio/pyproject.toml`、`studio/web/scripts/` | `check_distribution.py`、`check_installation.py`；编译资源随独立包分发，前端源码改动后拒绝陈旧构建 |
| `studio-vendored-charts` | `studio/vendor/lightweight-charts/`、`studio/vendor-metadata/` | `check_vendor.py`、上游单元／类型检查、`chart/triangle.test.ts`；完整 1,534 文件基线和四项本地修改可复核 |
| `studio-workspace-host` | `studio/src/openbacktesting_studio/cli.py`、`host/`、`protocol/` | `test_cli.py`、`test_host.py`、`test_protocol.py`；回环、会话、来源、协议、能力、只读隔离与真实端口 |
| `studio-source-editor` | `workspace/`、`features/CodeEditor.tsx`、`editor-state.ts` | `test_workspace.py`、`editor-state.test.ts`、`workflow.test.ts`；版本化保存、冲突保留、稳定源码快照与编辑器快捷键 |
| `studio-strategy-configuration` | `execution/data.py`、`worker.py`、`workspace/configuration.py`、`features/*Form.tsx` | `test_data.py`、`test_configuration.py`、`test_worker.py`、`inputs.test.ts`、`components.test.tsx`；九种输入、预设、稀疏属性、显式数据与无 pickle 快照 |
| `studio-run-lifecycle` | `execution/manager.py`、`execution/process.py` | `test_runs.py`、`test_worker.py`、`test_host.py`；新进程、单活动槽、幂等、取消竞争、真实阶段、有界日志和重启中断 |
| `studio-run-artifacts` | `artifacts/`、`host/reports.py` | `test_artifacts.py`、`test_reports.py`、`test_runs.py`；摘要、原子发布、受限导入、默认分享范围、来源预检与父运行 |
| `studio-chart-rendering` | `web/src/chart/`、`host/projection.py` | `model.test.ts`、`sync.test.ts`、`triangle.test.ts`、`test_reports.py`；精确时间、缺口／偏移／交叉／阶梯、着色、独立成交、聚合成员与同步 |
| `studio-results-report` | `host/reports.py`、`features/ReportView.tsx`、`EquityChart.tsx`、`LogPanel.tsx` | `test_reports.py`、`report.test.ts`、`components.test.tsx`；核心指标、不可用值、方向贡献、末根双观测与无序盘中边界 |
| `studio-ui-design` | `web/src/App.tsx`、`components/ui/`、`index.css` | 前端 typecheck／lint、`components.test.tsx`、`layout.test.ts`、`workflow.test.ts`；shadcn 控件、TradingView 式工作区、主题、布局和草稿／结果身份隔离 |

## 已执行检查

- 核心输入、运行时、Portfolio、Plotting、包身份及语言规则回归：176 项通过，20 条既有警告。命令：`.venv/bin/python -m pytest tests/test_input_runtime.py tests/test_script_runtime.py tests/test_portfolio.py tests/test_plotting.py tests/test_package_identity.py tests/test_language_check.py -q`。
- Studio 宿主测试：68 项通过，1 条 Starlette 测试客户端依赖弃用警告；包含真实 HTTP、短进程、失败持久化、排队 CSV 快照和快照重跑。
- Python 静态检查通过：`.venv/bin/ruff check studio/src studio/tests studio/scripts studio/hatch_build.py` 和对应 `ruff format --check`（Ruff 0.17.0，30 个文件）。
- 前端 typecheck／lint 通过；无浏览器测试 30 项通过，覆盖实际组件服务端渲染、纯状态和几何模型。
- 上游 Lightweight Charts 保留的 144 项单元测试和类型检查通过；本地三角形几何／命中回归通过。
- 最新官方稳定基线为 `v5.2.1`，提交 `b2ce010e4ad59f6556c9ed60e2b2b30feccdd2d1`；核验日期 2026-10-14。逐文件摘要检查通过。
- Studio 测试命令：`studio/.venv/bin/python -m pytest studio/tests -q`；前端命令：`npm --prefix studio/web run typecheck`、`npm --prefix studio/web run lint`、`npm --prefix studio/web test`、`npm --prefix studio/web run build`，全部通过。前端为 10 个测试文件；构建生成 19 项本地资源。
- 构建命令：`uv build`、`uv build studio --out-dir studio/dist`。`studio/.venv/bin/python studio/scripts/check_distribution.py studio/dist/*.whl studio/dist/*.tar.gz` 通过：Studio wheel 为 46 项、1,261,279 字节；sdist 为 68 项、1,455,791 字节。数字是压缩安装产物大小，不含 Python 依赖。核心 wheel／sdist 分别为 350／832 项，未包含 Studio 或前端开发树。
- `studio/.venv/bin/python studio/scripts/check_installation.py` 通过：在仓库外的两个干净环境分别安装核心 wheel／sdist，执行核心回测并读取包内资源，确认 Studio 尚未安装；再安装对应 Studio 产物，通过真实 HTTP 验证工作区执行、只读查看、本地静态入口、图表来源、Monaco Worker 和默认导出范围。安装及运行时的 `PATH` 均不包含 Node；运行时禁止对外连接，使用 `--no-open`，无浏览器渲染。
- 连续前端构建的资源摘要和输入摘要一致。对解包后的 sdist 增加未构建前端文件、另一次篡改编译后的 JS，Python 构建分别拒绝源码清单漂移和静态资源摘要不符。用户 sdist 安装不触发 Node 构建。
- `studio/.venv/bin/python studio/scripts/check_vendor.py` 核对完整来源与本地修改；`studio/.venv/bin/python studio/scripts/export_schemas.py` 重新生成协议 schema 并核对无漂移。`python3 scripts/check_package.py --artifact dist/openbacktesting-0.2.0-py3-none-any.whl --artifact dist/openbacktesting-0.2.0.tar.gz`、`python3 scripts/check_language.py`、`git diff --check` 和 `openspec validate add-openbacktesting-studio --strict` 均通过。
- 已逐项对照本变更的 Requirement／Scenario、任务与上表能力责任。完成记录覆盖实现与本节实际执行的检查；不将静态组件检查解释为视觉验收。

## 本地测量

命令：`studio/.venv/bin/python studio/scripts/measure_projection.py`。机器环境为 macOS 26.5、arm64、Python 3.13.12；下列为一次本地样例，不构成容量或延迟承诺。

| 项目 | 规模与结果 |
| --- | --- |
| 序列投影 | 50,000 根合成 K 线、0 个指标来源，显示预算 5,000；返回 1,640 点，聚合粒度 61，约 27.5 毫秒，JSON 393,695 字节 |
| 报告 HTTP | 120 根样例数据，响应约 373.1 毫秒，32,217 字节；包含本地请求路径开销 |
| 全部静态资源 | 4,210,002 字节 |
| 入口 JS＋CSS | 746,662 字节；计算所得 gzip 体积 224,526 字节，不代表宿主已启用 gzip 传输 |
| 延迟编辑器资源 | 2,817,522 字节；编辑器按需加载，构建器仍提示大分块 |

## 确定的边界与权衡

- 执行可信本地 Python，工作进程不是安全沙箱。归档导入不会执行其中的源码；历史快照重跑仅适用于本地可信运行，且要求源码、数据、请求和环境预检通过。
- 工作区代码保存在实际本地文件；参数和回测属性保存为请求／预设，不重写 `.py` 默认值。外部变更通过两秒轮询发现，脏缓冲区保留草稿。
- 图表轴以原始 bar 身份定位，纳秒时间标签不截断后充当键；naive／ordinal 标签不伪造日期。聚合仅用于显示，事实仍按原 ID 分页访问。
- 聚合保留 OHLCV、指标极值、缺口与交叉边界；语义细节超过预算时明确拒绝该显示范围。颜色代表值取桶内最后事件，不向下一桶继承。
- 权益显示曲线与权威指标分离。末根 terminal 只替换绘制点，原始两个观测保留；无序盘中边界不拼成轨迹。
- 包内提供静态资源和本地编辑器 Worker，无 CDN。完整图表开发树只留在仓库，不进入用户 Python 包。
- 当前验证平台为 macOS；Python 测试环境为 3.13.12，核心回归环境为 3.12.12，Node 为 22.23.2。Linux／Windows 未执行；文件保护使用 POSIX 目录描述符，不声称 Windows 支持已完成。
- 初次实施未执行浏览器 E2E、截图／视觉验收或真实浏览器无障碍审计。后续浏览器验证范围见下节；仍不将单个样例的人工验证解释为全量视觉或无障碍验收。
- 未发布 PyPI、未部署、未自动提交 Git 或创建 PR。

## 后续浏览器验证：首次运行流程

- 用户反馈 Run 无法正常使用后，在用户当前 Chrome 标签页复现：首次 Run 先要求确认 schema，再进入设置，原来的 Apply to next run 仅关闭弹窗，必须再次点击 Run。该样例未观察到后端执行异常，但确认流程中断了用户的运行意图。
- 修复为首次 Run 直接打开策略设置，使用 Apply & Run 确认后继续保存／发现／验证／提交；单独打开设置仍只应用配置，schema 变更仍要求明确审阅。
- 2026-10-14，在原有本地 Studio 服务上重新加载构建，搜索并选择 `examples/strategies/first_backtest.py`，点击 Run，再点击 Apply & Run；无需第三次点击，新运行 `75e4ea37` 为 succeeded，显示 2,148 根 K 线、权益曲线与报告，报告总收益率 249.66%。浏览器错误日志为空，已取得实际页面截图。
- 本轮 typecheck、lint、30 项前端测试与 build 通过。这是 macOS Chrome 上的单个真实工作流验证，不覆盖全部策略、浏览器或无障碍行为。

## 后续修复：目录选择与历史结果

- 启动目录改为选择器的初始浏览位置，不自动创建工作区状态或扫描文件。新增受会话保护的目录浏览与选择 API；只有明确选择后才建立该工作区的管理器。前端用 `studio.workspace` 保存路径，默认固定端口 8765，支持 `--port 0`，并明确 localStorage 不能跨来源共享。
- 切换工作区等待已接收请求结束，拒绝活动／排队运行；UI 阻止未保存草稿切换。工作区身份随请求传递，旧标签页不能把相对路径写入新目录。只读模式不提供目录选择接口。
- 在用户 Chrome 页面复现历史记录缺陷：重复点击当前成功 Run 会清空已加载结果并取消请求，但 selected ID 未变化，因此读取 effect 不再执行。已增加相同选择保护、按运行和资源缓存以及明确的读取失败／超时状态。
- 浏览器验证：首次弹出目录选择器；选择 `examples/strategies` 后只显示 17 个策略文件；刷新和宿主实际重启后均恢复该目录。切换回原仓库仍可查看已有的四条历史记录；重复点击 `5415fe03` 和在 `75e4ea37`／`5415fe03` 之间切换均正常，缓存命中时没有 Loading。切回策略目录并执行 `first_backtest.py`，新运行 `a8633dc0` 成功，图表和报告正常。原目录历史保留，没有迁移或删除。
- Studio 后端 70 项、前端 30 项测试通过；类型、lint 和构建通过。CLI 及端口占用保护另有 5 项针对性检查通过。wheel／sdist 均已通过无 Node 的干净安装、手动选择工作区、真实执行及只读查看检查。上述浏览器证据只覆盖实际操作的流程，不代表全面视觉或无障碍验收。
