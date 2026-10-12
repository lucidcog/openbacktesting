# 参数实验与本地结果集

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

参数实验固定当前配置，逐组保存完整 Portfolio；结果集支持重开、筛选和排序。

[使用指南](../guides/optimizer.md) · [兼容与内部入口](classification.md)

<a id="openbacktesting-optimizer-executionidentity"></a>

## ExecutionIdentity

完整对象：`openbacktesting.optimizer.ExecutionIdentity`

```python
openbacktesting.optimizer.ExecutionIdentity(strategy_sha256: 'str', dependencies_sha256: 'str') -> None
```

宿主对已加载源码及本地依赖的 SHA256 声明，不加载或执行文件。

源码：`src/openbacktesting/optimizer/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `strategy_sha256` | `str` |
| `dependencies_sha256` | `str` |

<a id="openbacktesting-optimizer-experimentresult"></a>

## ExperimentResult

完整对象：`openbacktesting.optimizer.ExperimentResult`

```python
openbacktesting.optimizer.ExperimentResult(path: str, experiment_id: str) -> None
```

可重开的只读结果集句柄；每次访问独立连接，无活策略引用。

源码：`src/openbacktesting/optimizer/query.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `path` | `<class 'str'>` |
| `experiment_id` | `<class 'str'>` |

<a id="openbacktesting-optimizer-experimentresult-backup"></a>

### backup

完整对象：`openbacktesting.optimizer.ExperimentResult.backup`

```python
openbacktesting.optimizer.ExperimentResult.backup(self, destination) -> str
```

一致性备份到新本地文件，拒绝覆盖已有文件。

源码：`src/openbacktesting/optimizer/query.py`。

<a id="openbacktesting-optimizer-experimentresult-fields"></a>

### fields

完整对象：`openbacktesting.optimizer.ExperimentResult.fields`

```python
openbacktesting.optimizer.ExperimentResult.fields(self) -> list[dict]
```

返回标量的路径、类型、单位、状态、方法与建议排序方向。

源码：`src/openbacktesting/optimizer/query.py`。

<a id="openbacktesting-optimizer-experimentresult-info"></a>

### info

完整对象：`openbacktesting.optimizer.ExperimentResult.info`

```python
openbacktesting.optimizer.ExperimentResult.info(self) -> dict
```

返回实验状态、分类计数及不可变计划副本。

源码：`src/openbacktesting/optimizer/query.py`。

<a id="openbacktesting-optimizer-experimentresult-load-portfolio"></a>

### load_portfolio

完整对象：`openbacktesting.optimizer.ExperimentResult.load_portfolio`

```python
openbacktesting.optimizer.ExperimentResult.load_portfolio(self, trial_id: str) -> dict
```

校验并加载单份完整报告，失败或损坏时明确拒绝。

源码：`src/openbacktesting/optimizer/query.py`。

<a id="openbacktesting-optimizer-experimentresult-query"></a>

### query

完整对象：`openbacktesting.optimizer.ExperimentResult.query`

```python
openbacktesting.optimizer.ExperimentResult.query(self, *, order_by=(), filters=(), fields=(), limit: int = 100, cursor: str | None = None) -> dict
```

查询成功组的标量与参数；游标固定提交范围，重新查询刷新。

order_by 为路径或 (路径, asc/desc)，filters 为 (路径, 运算符, 值)。
运算符支持 eq/ne/lt/le/gt/ge/status；点号和反斜杠键需反斜杠转义。

源码：`src/openbacktesting/optimizer/query.py`。

<a id="openbacktesting-optimizer-experimentresult-trials"></a>

### trials

完整对象：`openbacktesting.optimizer.ExperimentResult.trials`

```python
openbacktesting.optimizer.ExperimentResult.trials(self, *, limit: int = 100, offset: int = 0) -> list[dict]
```

分页浏览所有已访问试验的实时状态，不附带完整 Portfolio。

源码：`src/openbacktesting/optimizer/query.py`。

<a id="openbacktesting-optimizer-optimizationerror"></a>

## OptimizationError

完整对象：`openbacktesting.optimizer.OptimizationError`

```python
openbacktesting.optimizer.OptimizationError(message, path, experiment_id, committed)
```

实验基础设施错误，保留结果位置、身份及最后已知提交数。

源码：`src/openbacktesting/optimizer/models.py`。

<a id="openbacktesting-optimizer-plan"></a>

## Plan

完整对象：`openbacktesting.optimizer.Plan`

```python
openbacktesting.optimizer.Plan(_json: 'str') -> None
```

不可变规范文本；snapshot 返回独立副本，组合在运行时逐项产生。

源码：`src/openbacktesting/optimizer/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |

<a id="openbacktesting-optimizer-plan-snapshot"></a>

### snapshot

完整对象：`openbacktesting.optimizer.Plan.snapshot`

```python
openbacktesting.optimizer.Plan.snapshot(self) -> 'dict'
```

返回完整计划的独立 JSON 副本。

源码：`src/openbacktesting/optimizer/models.py`。

<a id="openbacktesting-optimizer-plan-total"></a>

### total

完整对象：`openbacktesting.optimizer.Plan.total`

```python
openbacktesting.optimizer.Plan.total(self) -> 'int'
```

原始笛卡尔积数量，不扣除尚未检查的约束。

源码：`src/openbacktesting/optimizer/models.py`。

<a id="openbacktesting-optimizer-range"></a>

## Range

完整对象：`openbacktesting.optimizer.Range`

```python
openbacktesting.optimizer.Range(start: 'int | str', stop: 'int | str', step: 'int | str') -> None
```

升序格点范围；int 使用整数，float/price 使用十进制字符串或整数。

源码：`src/openbacktesting/optimizer/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `start` | `int \| str` |
| `stop` | `int \| str` |
| `step` | `int \| str` |

<a id="openbacktesting-optimizer-values"></a>

## Values

完整对象：`openbacktesting.optimizer.Values`

```python
openbacktesting.optimizer.Values(values: 'tuple | list') -> None
```

有限候选值；由 plan 按对应 input 声明校验。

源码：`src/openbacktesting/optimizer/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `values` | `tuple \| list` |

<a id="openbacktesting-optimizer-execute"></a>

## execute

完整对象：`openbacktesting.optimizer.execute`

```python
openbacktesting.optimizer.execute(plan_value, executor, path, *, experiment_id=None, constraint=None, cancel=None, on_progress=None)
```

执行或恢复计划；executor 接收标题请求并返回完整 Portfolio 字典。

约束接收完整 wire 值，cancel 是无参 bool callable；on_progress 只消费通知。
仅显式 experiment_id 表示恢复；失败组不自动重试。

源码：`src/openbacktesting/optimizer/runner.py`。

<a id="openbacktesting-optimizer-open-result"></a>

## open_result

完整对象：`openbacktesting.optimizer.open_result`

```python
openbacktesting.optimizer.open_result(path, experiment_id: str | None = None) -> openbacktesting.optimizer.query.ExperimentResult
```

只读打开一个实验结果库，无策略或行情依赖。

源码：`src/openbacktesting/optimizer/query.py`。

<a id="openbacktesting-optimizer-plan-function"></a>

## plan

完整对象：`openbacktesting.optimizer.plan`

```python
openbacktesting.optimizer.plan(strategy_class, search: collections.abc.Mapping[str, openbacktesting.optimizer.models.Values | openbacktesting.optimizer.models.Range], *, base_inputs=None, execution: collections.abc.Mapping, constraint_id: str | None = None) -> openbacktesting.optimizer.models.Plan
```

冻结完整当前配置与选定维度；执行身份必须由宿主明确提供。

Args:
    strategy_class: 已加载并声明 inputs 的策略类。
    search: 按唯一标题指定的非空搜索域。
    base_inputs: 既有标题请求；None 使用声明默认值。
    execution: 已规范化的代码、行情、配置和版本身份。
    constraint_id: 可选受信任约束的版本摘要，不序列化函数。

源码：`src/openbacktesting/optimizer/plan.py`。
