# 品牌实施记录

## 范围清单

| 位置 | 原状与处理目标 | 状态 |
| --- | --- | --- |
| Studio 顶栏 | Activity 与普通文字 → 共享字标，窄屏紧凑版 | 已替换并验证 |
| Studio favicon | 未声明 → 同源紧凑标识 | 已替换并验证 |
| Docs 页头、移动抽屉与 favicon | 系统文字和 Material 通用图标 → 共享字标及紧凑标识 | 已替换并验证 |
| `README.md` | 文本标题 → 增加明暗字标，保留标题 | 已替换并验证 |
| `docs/readme/README.{zh-CN,es,pt-BR,fr,de,it,hi}.md` | 七种语言入口增加共享字标 | 已替换并验证 |
| `studio/README.md` | 增加共享字标 | 已替换并验证 |
| `docs/core/_static/studio/` | 七张当前截图逐一检查、真实重拍旧品牌 | 已替换并验证 |
| 其他第一方文档 | `examples/README.md` 等是文字说明，无独立 Logo；正文名称保留 | 已检查 |
| Pineify / TradingView / vendor | 第三方品牌和归因保留 | 已确认边界 |

## 验证证据

- Manrope 800、-0.015em 字距与局部光学校正，正式字标比率 8.3333:1；Studio 18px 字形高度，Docs 桌面 24px、窄屏 18px。小屏及 favicon 使用同源 `OB`。
- 来源固定于 Google Fonts 提交 `94301472b4d809299b4775bc6502592b83dd6934`，字体与授权摘要见 `docs/assets/brand/*-source.json`；无运行时新字体依赖。
- 已人工查看 1×/2× 字标样张及 16/32px favicon；浏览器样张见 `.verification/brand/evidence/brand-preview*.png`，原始对照见 `.verification/brand/specimen.html`。
- Studio 与 Docs 已覆盖 1440/768/375/320 CSS px、浅色/深色主题。Docs 首轮在 375px 溢出 9px，调整为 150px 宽字标后复验通过。结果见 `.verification/brand/studio-results.json`、`.verification/brand/docs-results.json`。
- 使用隔离 Chromium 扩展的 `chrome.tabs.setZoom(..., 2)` 验证实际 200% 标签页缩放，1440/768px 视口分别得到 720/384 CSS px 与 DPR 2。证据见 `.verification/brand/zoom-results.json`，不是 CSS 缩放替代。
- README 使用 Python-Markdown 3.11 在本地 Chromium 中渲染，完成根目录、中文、德语及 Studio 的明暗预览和主题选择缺失回退；其余译本通过路径检查。将字标置于语义一级标题中，避免重复大标题；正文保留文本品牌名称。未验证 GitHub 原生渲染。
- 七张产品截图均从隔离目录中的真实 EMA、日志策略及六组合优化器运行重新拍摄，保留完整 TradingView 归因。Activity 在空图表中的剩余使用是状态图示，不是品牌。
- Docs 预览另观察到嵌套页请求相对 `sitemap.xml` 返回 404；品牌资源、首页导航、搜索和抽屉通过检查。现有 GitHub 统计请求还受到公共 API 限流。两者不作为品牌资产通过证据，也未修改无关逻辑。
- 文档共享资源与九份 README 路径的集成测试通过；全仓最终验证已通过。线上部署不在本次实施范围内。

## 迁移清单的定点维护

首轮全仓检查发现 README 的目标摘要不匹配，已取消该轮以先修复。核对确认原摘要与 `HEAD:README.md` 一致，差异仅为已授权的品牌标题替换；因此只更新 `extraction-manifest.json` 中 `README.md` 的 `targetSha256` 并追加英文变更原因。`sourceSha256`、`sourceRevision`、历史来源清单、数值及 schema 基线保持不变。

## 最终验收

- `uv run --locked python scripts/verify.py --profile full`：通过，包含核心回归 3203 passed / 1 skipped、Studio 后端 148 passed、前端 397 passed、浏览器检查 6 passed，以及分发和隔离安装验证。
- 完整结果：`.verification/harness/20261015T140041Z-0f5a6ce9a1/result.json`；首轮摘要失配后取消的记录保留于 `.verification/harness/20261015T135801Z-5f66bb15bc/`。
- Docs 375px 溢出已修复；移动抽屉的默认 Material 标识已改为共享 favicon，并检查实际展开状态。实际浏览器标签的 `favIconUrl` 已核验，两端均采用新图标。
- 浏览器资源、视口与主题检查结果保存在 `.verification/brand/*-results.json`；人工检查的图像位于 `.verification/brand/evidence/`。这些本地证据不进入分发包，当前产品截图随仓库交付。
- 浏览器验收所用临时服务、隔离工作区及本地会话凭据已清理。线上 Docs 未部署，GitHub 原生 README 渲染未验收；本地代码与资源替换已完成。
