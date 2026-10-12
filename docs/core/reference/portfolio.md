# Portfolio报告与冻结导出

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

公开对象参考。

[使用指南](../index.md) · [兼容与内部入口](classification.md)

<a id="openbacktesting-portfolio-portfoliosnapshot"></a>

## PortfolioSnapshot

完整对象：`openbacktesting.portfolio.PortfolioSnapshot`

```python
openbacktesting.portfolio.PortfolioSnapshot(payload: str)
```

不可变的版本化事实文本；通过to_dict读取完整报告。

快照不持有策略、pandas或可变输入。派生分析只读取已冻结事实；
文本自身是内部存储格式，跨语言消费使用export_result的报告。

源码：`src/openbacktesting/portfolio/snapshot.py`。

<a id="openbacktesting-portfolio-portfoliosnapshot-to-dict"></a>

### to_dict

完整对象：`openbacktesting.portfolio.PortfolioSnapshot.to_dict`

```python
openbacktesting.portfolio.PortfolioSnapshot.to_dict(self) -> dict
```

计算并返回独立的严格JSON报告；不修改快照或执行策略。

源码：`src/openbacktesting/portfolio/snapshot.py`。

<a id="openbacktesting-portfolio-export-result"></a>

## export_result

完整对象：`openbacktesting.portfolio.export_result`

```python
openbacktesting.portfolio.export_result(result: pandas.Series) -> dict
```

返回完整报告的独立纯值副本；无文件、网络和绘图副作用。

源码：`src/openbacktesting/portfolio/snapshot.py`。

<a id="openbacktesting-portfolio-get-snapshot"></a>

## get_snapshot

完整对象：`openbacktesting.portfolio.get_snapshot`

```python
openbacktesting.portfolio.get_snapshot(result: pandas.Series) -> openbacktesting.portfolio.snapshot.PortfolioSnapshot
```

读取冻结事实快照；旧结果或交易子集缺少完整事实时明确拒绝。

Raises:
    ValueError: 结果未采集Portfolio。

源码：`src/openbacktesting/portfolio/snapshot.py`。

<a id="openbacktesting-portfolio-report-catalog"></a>

## report_catalog

完整对象：`openbacktesting.portfolio.report_catalog`

```python
openbacktesting.portfolio.report_catalog() -> dict
```

返回报告字段目录的独立副本，供宿主核对覆盖与方法身份。

源码：`src/openbacktesting/portfolio/__init__.py`。
