# 抽离验收记录

2026-10-12 完成独立包抽离与验收。验证范围为 macOS ARM64、Python `3.12.12`；本记录不代表其他 Python 版本或平台已验收。

## 回归结果

- `python -m pytest`：`2877 passed, 1 skipped`，耗时 `62.03s`；跳过项为默认关闭的完整 ML 慢例，输出含 `170 warnings`。
- 在独立解压的 sdist 中、使用 site-packages 内已安装包及与基线一致的依赖运行完整套件：`2877 passed, 1 skipped`，耗时 `64.88s`，输出含 `170 warnings`。测试及夹具没有依赖原仓库或当前源码目录。
- `python -m openbacktesting.test`：运行 `67` 项，`OK (skipped=1)`，耗时 `13.955s`；跳过项是仅在 Linux 执行的 `TestDocs.test_examples`，其日志原因为 `test_examples requires mp.start_method=fork`。pytest 中的示例套件已执行。
- 最终示例索引适配后，单独复核 `test_index_and_execution_sets_match` 通过。
- `ruff check scripts`、`ruff format --check scripts`、指标方法生成物与 API 文档一致性检查通过。

源码回归环境为 NumPy `2.5.3`、pandas `3.0.6`、`pandas-ta-classic 0.8.32`、pytest `9.1.1`、SAMBO `1.25.2`、scikit-learn `1.9.1`。独立安装环境按依赖范围解析到 NumPy `2.5.4`，其余基础计算依赖版本相同。

原指标基线同时精确核对依赖版本元数据；未锁定的 NumPy `2.5.4` 环境出现 `179` 项版本字段断言失败，而对应数值断言通过。固定为基线使用的 `2.5.3` 后完整通过。sdist 已纳入当前项目 `uv.lock`，供开发者按锁定环境复现；未放宽断言或修改版本基线。

## 分发与身份

`uv build --no-sources` 生成 wheel 和 sdist。在两个不同的干净环境中分别直接安装 wheel，以及从独立解压的 sdist 重建后安装 wheel；清除 `PYTHONPATH` 和 `PYTHONHOME`，以 `python -I` 从不含源码的目录运行 `scripts/verify_installation.py` 对应探针。

两条安装路径均确认从 site-packages 加载唯一新包身份，并通过运行资源读取、最小回测、pickle 往返、spawn 传输、Portfolio 保存读取、优化实验取消与恢复、不匹配身份拒绝续跑及已有存档内容保持检查。基础环境缺少可选优化器时返回明确依赖错误；安装制品的 `optimize` extra 后，SAMBO 最小优化成功。

独立安装暴露了 SAMBO 顶层导入依赖缺口：源包的测试环境提供了 scikit-learn/joblib，原 `optimize` 声明却未包含。现已补入已有测试使用的 `scikit-learn>=1.5,<2` 范围，由其引入 joblib；基础依赖与计算算法未调整。

## 迁移一致性与只读边界

346 个运行时文件与直接源快照逐文件对照，仅包含约定的身份和路径替换。3 份 Base64 pickle 夹具只规范化身份字符串并更新长度、帧和摘要；除字符串编码与帧封装外，其他操作码字节逐项比对一致，没有重生成历史数值预期。名称检查覆盖这些编码夹具的解码内容。

源仓库提交保持为 `844bae116047a7b6cf3fe400ab0b98910ccb729b`。对 2107 个已记录文件（含核心目录已有缓存）复核摘要，全部一致；源 Git 工作区仍干净。所有迁移、构建、测试及安装验证文件写入当前仓库。

`scripts/check_package.py` 检查项目文件、清单、Python 语法、文档链接和制品成员，旧项目名及旧包名的大小写不敏感扫描零命中。文档、OpenSpec、元数据和编码夹具均在检查范围内；缓存和验证环境不进入分发制品。

## 未验证项

Python `3.13/3.14`、其他操作系统、完整 ML 慢例及 Pine 等价行为未验收。本次提供本地制品，不包含上传、包注册平台发布或原工程消费者迁移。
