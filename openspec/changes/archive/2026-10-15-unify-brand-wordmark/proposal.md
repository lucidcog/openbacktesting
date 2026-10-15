## Why

当前 OpenBacktesting 在 Studio、Docs 网站和 README 中分别使用普通界面文字、通用图标或标题，缺少统一且可辨识的文字品牌。用户已确认研究推荐的 Manrope 几何粗字标方向，并要求覆盖现有品牌展示位置、README、Docs 网站及浏览器验收。

## What Changes

- 以 Manrope 750–800 为起点设计原创 `OpenBacktesting` 字标，保留大小写节奏，经过实际尺寸比较确定字重和光学字距；Inter 仅作为对照样张。
- 建立单一资产来源，提供浅色、深色背景可用的矢量字标，以及用于 favicon 和极窄空间的同源紧凑标识；记录字体来源、版本、授权和导出方法。
- 统一 Studio 顶栏、Docs 网站页头和浏览器图标；为根 README、各语言 README 和 Studio README 添加品牌资产，核对其他第一方可见品牌入口并完成清单。
- 更新当前文档中展示旧品牌的产品截图，保留历史记录及第三方原始素材；普通正文中的产品名称不批量替换成图片。
- 根据用户明确提出的浏览器验收要求，验证 Studio、Docs 与 README 预览的品牌渲染、主题切换、窄屏布局和相关导航，保存有限且可追溯的证据。

## Capabilities

### New Capabilities

- `brand-identity`：统一品牌资产、跨载体展示、响应式与无障碍约束，以及品牌替换完整性和浏览器验收。

### Modified Capabilities

无。当前没有可修改的 `openspec/specs/` 规范；本变更不改变交易、回测或宿主协议。

## Impact

- 主要影响 `docs/assets/`、`studio/web/src/`、`studio/web/index.html`、必要的前端资源构建接入、`docs/theme/`、`docs/core/_static/`、`mkdocs.yml`、`scripts/docs_site.py`、第一方 README 及相关文档与布局检查。
- 运行时只消费本地品牌资产，不要求额外远程字体请求或修改全站界面字体；发布资产必须进入现有 Docs 构建和 Studio 分发产物。
- Pineify 赞助商标识、TradingView 图表归因及 vendor 文件保持其第三方身份。名称、包名、API、数值基线及现有产品文案语言不变。
- 本阶段只形成中文提案、设计、规范和任务，并按精确路径与摘要登记语言例外；实现及浏览器验收在后续执行阶段完成。
