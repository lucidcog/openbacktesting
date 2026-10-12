# 实施与验证

本次实施完成独立包抽离，唯一发行与导入身份为 `openbacktesting`，版本为 `0.2.0`。原仓库未改动；公开计算行为保留，旧身份兼容边界按设计执行。

## 实际结果

- 根级 Python 项目、源码、资源、测试、示例、内核手册及独立检查工具已落地。
- 现有 pytest 回归为 `2877 passed, 1 skipped`；包内自测为 `67` 项、`OK (skipped=1)`。
- 独立解压 sdist、使用安装包和基线依赖运行的完整 pytest 同样为 `2877 passed, 1 skipped`；sdist 携带当前项目锁文件以复现版本元数据基线。
- wheel 直接安装与 sdist 重建安装均通过资源、回测、pickle、spawn、优化持久化和基础/可选依赖边界验证。
- 346 个运行时文件仅作身份与路径替换；3 份编码 pickle 基线除字符串编码与帧封装外的操作码字节保持一致。
- 2107 个源文件摘要、源提交和 Git 工作区状态复核一致。

## 实施中修正

独立环境发现 SAMBO 的顶层导入需要 scikit-learn/joblib，源 `optimize` extra 未声明且被 `test` 环境掩盖。已将 `scikit-learn>=1.5,<2` 补入 `optimize`，沿用已有测试范围；基础依赖、算法及数值基线未变。

已将文档生成工具适配为直接可读的 Markdown，修复原工程命令、历史链接和资源路径。网站构建配置未迁入，排除理由保存在清单中。

## 验证依据

环境、命令、结果及未验证范围见[验收记录](../../../../docs/core/extraction-verification.md)。验证平台为 macOS ARM64、Python `3.12.12`；其他 Python 版本、平台和完整 ML 慢例未验收。项目文件及 wheel/sdist 经名称与完整性扫描通过，未发布至包注册平台。
