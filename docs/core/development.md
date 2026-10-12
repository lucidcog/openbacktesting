# 内核开发与验证

公开行为变更需要同步指南、API 参考、可运行示例和验证。运行源码位于 `src/openbacktesting/`，按 data、broker、strategy、simulation、portfolio、optimizer、indicators 分工；公共入口由包自身导出。

## 环境与命令

在当前仓库根目录运行：

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
uv run --locked python scripts/generate_indicator_api.py --check
uv run --locked python scripts/core_docs.py --check
uv build --no-sources
uv run --locked python scripts/check_package.py --artifact dist/openbacktesting-0.2.0-py3-none-any.whl --artifact dist/openbacktesting-0.2.0.tar.gz
```

`uv.lock` 固定本仓库验证环境，并随 sdist 分发；独立安装根据 `pyproject.toml` 解析依赖，不要求该锁文件。解压 sdist 后用 `uv sync --locked --extra test` 建立环境，再运行相同 Python 测试命令。历史基线精确核对依赖版本字段，因此全量回归需要锁定环境，不能把其他依赖版本的身份差异当作数值回归。完整 ML 慢例通过 `OPENBACKTESTING_RUN_SLOW_EXAMPLES=1` 显式启用，默认不执行。

`optimize` extra 除 SAMBO 外还声明 scikit-learn，由其带入 joblib；这是当前 SAMBO 顶层导入所需的依赖，基础回测安装不增加这组依赖。

## 文档和生成接口

手册为可直接阅读的 Markdown，不需要网站构建。公开 API 清单位于 `api-manifest.json`，指标名称、用途和示例关系位于 `indicator-notes.json`。修改接口或目录后生成并检查：

```sh
uv run --locked python scripts/generate_indicator_api.py
uv run --locked python scripts/core_docs.py
uv run --locked python scripts/check_package.py
```

`generate_indicator_api.py` 根据固定目录生成指标方法；`core_docs.py` 根据已安装对象和目录生成 API 签名、docstring 与指标参考。手写指南不会被覆盖。机器检查确认结构一致，文字语义仍须审阅。

## 分发完整性

wheel 包含运行源码、`py.typed`、指标和 Portfolio 目录、结果 Schema 及内置 CSV 数据。sdist 额外提供测试、夹具、示例、手册、来源清单及本地检查工具。独立环境中应从不含源码的工作目录验证实际加载路径属于 site-packages，并执行最小回测、资源读取、pickle、spawn 与优化结果保存恢复。

`check_package.py` 扫描项目路径及内容，名称规则忽略大小写，覆盖文档、测试、OpenSpec 和制品元数据；同时检查文件清单、Python 语法与文档链接。禁止通过排除交付文件隐藏命中。

## 来源和行为边界

[历史来源清单](../../source-manifest.json) 保留早期上游来源证据；[本次抽离清单](../../extraction-manifest.json) 记录直接源快照及路径映射。来源路径按新身份规范化，来源摘要仍对应原始字节；目标摘要对应当前内容。

迁移保持 API 签名、计算值和事件顺序，只调整身份及路径。旧模块路径 pickle 不自动加载，旧品牌语义存档不保证可直接读取，旧实验不支持以新执行身份续跑；新身份数据支持正常保存、读取和恢复。详细使用限制见[当前限制](limitations.md)。

新增能力须扩展示例索引和实际执行验证，不能仅凭语法检查交付；内部重构应证明公开行为不变。此仓库不依赖桌面组件、父级 workspace 或 JavaScript 工具链。
