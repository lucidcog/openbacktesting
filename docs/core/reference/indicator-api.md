# 指标计算与结果句柄

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

策略通过 self.ta 登记指标；句柄按运行游标读取，显式转换产生快照。离线计算使用 compute。

[使用指南](../guides/indicators.md) · [兼容与内部入口](classification.md)

<a id="openbacktesting-indicators-default-cache-bytes"></a>

## DEFAULT_CACHE_BYTES

单个指标缓存的默认保留字节预算，不是进程内存上限。

`openbacktesting.indicators.DEFAULT_CACHE_BYTES` = `67108864`。

<a id="openbacktesting-indicators-indicatorcache"></a>

## IndicatorCache

完整对象：`openbacktesting.indicators.IndicatorCache`

```python
openbacktesting.indicators.IndicatorCache(budget=67108864)
```

预算是缓存保留量；活跃策略持有量不受这个预算限制。

源码：`src/openbacktesting/indicators/runtime.py`。

<a id="openbacktesting-indicators-indicatorcache-clear"></a>

### clear

完整对象：`openbacktesting.indicators.IndicatorCache.clear`

```python
openbacktesting.indicators.IndicatorCache.clear(self)
```

清空保留条目并归零保留字节数；不撤销活跃结果引用。

源码：`src/openbacktesting/indicators/runtime.py`。

<a id="openbacktesting-indicators-indicatorcache-get"></a>

### get

完整对象：`openbacktesting.indicators.IndicatorCache.get`

```python
openbacktesting.indicators.IndicatorCache.get(self, key, calculate)
```

使用 key 查找缓存，否则执行 calculate；同键并发合并，失败不缓存，返回只读模板。

源码：`src/openbacktesting/indicators/runtime.py`。

<a id="openbacktesting-indicators-api-indicatorresult"></a>

## IndicatorResult

完整对象：`openbacktesting.indicators.api.IndicatorResult`

```python
openbacktesting.indicators.api.IndicatorResult(handle: openbacktesting.indicators.types.IndicatorHandle)
```

多输出的只读属性容器；通道视图只在初始化时创建。

源码：`src/openbacktesting/indicators/api.py`。

<a id="openbacktesting-indicators-api-indicatorresult-df"></a>

### df

完整对象：`openbacktesting.indicators.api.IndicatorResult.df`

```python
openbacktesting.indicators.api.IndicatorResult.df(self)
```

返回全部通道当前前缀的 pandas DataFrame 副本。

源码：`src/openbacktesting/indicators/api.py`。

<a id="openbacktesting-indicators-api-indicatorresult-metadata"></a>

### metadata

完整对象：`openbacktesting.indicators.api.IndicatorResult.metadata`

```python
openbacktesting.indicators.api.IndicatorResult.metadata(self)
```

返回底层句柄来源元数据的独立副本。

源码：`src/openbacktesting/indicators/api.py`。

<a id="openbacktesting-indicators-api-indicatorresult-ready"></a>

### ready

完整对象：`openbacktesting.indicators.api.IndicatorResult.ready`

```python
openbacktesting.indicators.api.IndicatorResult.ready(self)
```

各输出共享的最低历史条件掩码。

源码：`src/openbacktesting/indicators/api.py`。

<a id="openbacktesting-indicators-api-indicatorresult-valid"></a>

### valid

完整对象：`openbacktesting.indicators.api.IndicatorResult.valid`

```python
openbacktesting.indicators.api.IndicatorResult.valid(self)
```

底层各通道的有效性掩码；交易前优先检查所选通道。

源码：`src/openbacktesting/indicators/api.py`。

<a id="openbacktesting-indicators-catalog"></a>

## catalog

完整对象：`openbacktesting.indicators.catalog`

```python
openbacktesting.indicators.catalog()
```

返回全部已审核定义的元组，包括不可调用的延期项。

Returns:
    tuple: 指标定义；调用前检查 status，数量随审核目录变化。

源码：`src/openbacktesting/indicators/runtime.py`。

<a id="openbacktesting-indicators-compute"></a>

## compute

完整对象：`openbacktesting.indicators.compute`

```python
openbacktesting.indicators.compute(indicator, frame, *, parameters=None, backend=None, inputs=None, cache=None, cursor=None, required_outputs=None)
```

对显式行情批量计算已审核指标，返回只读结果句柄。

Args:
    indicator: 完整目录 ID。
    frame: pandas DataFrame；索引和输入必须满足指标契约。
    parameters: 参数映射；未知键、非法类型和关系均拒绝。
    backend: 后端标识；None 使用目录默认值，不静默回退。
    inputs: 指标输入到行情列名或同运行单通道的映射。
    cache: 可选 IndicatorCache；None 每次重新计算。
    cursor: 框架内部运行游标；独立计算保留 None。
    required_outputs: 必要输出规范名；空列表关闭预热门控。

Returns:
    IndicatorHandle: 单通道或多通道句柄，具有 valid/ready 与来源 metadata。

Raises:
    IndicatorError: ID、参数、后端、输入、输出或计算失败。

源码：`src/openbacktesting/indicators/runtime.py`。

<a id="openbacktesting-indicators-describe"></a>

## describe

完整对象：`openbacktesting.indicators.describe`

```python
openbacktesting.indicators.describe(indicator)
```

按稳定 ID 查询指标定义，不执行计算。

Args:
    indicator: 目录中的完整 ID，例如 ta.ema。

Returns:
    IndicatorSpec: 参数域、输出、状态及语义版本定义。

Raises:
    IndicatorError: ID 不存在时 code 为 unknown-indicator。

源码：`src/openbacktesting/indicators/runtime.py`。

<a id="openbacktesting-indicators-types-indicatorhandle"></a>

## IndicatorHandle

完整对象：`openbacktesting.indicators.types.IndicatorHandle`

```python
openbacktesting.indicators.types.IndicatorHandle(values, *, name, index, cursor=None, valid=None, required=None, metadata=None, ready=None)
```

时间维在最后；所有派生视图在读取时才应用游标和选择器。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-astype"></a>

### astype

完整对象：`openbacktesting.indicators.types.IndicatorHandle.astype`

```python
openbacktesting.indicators.types.IndicatorHandle.astype(self, dtype)
```

按 dtype 转换当前前缀为 NumPy 数组快照，不保留动态游标。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-copy"></a>

### copy

完整对象：`openbacktesting.indicators.types.IndicatorHandle.copy`

```python
openbacktesting.indicators.types.IndicatorHandle.copy(self)
```

返回当前前缀的可写 NumPy 副本，不再跟随游标。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-df"></a>

### df

完整对象：`openbacktesting.indicators.types.IndicatorHandle.df`

```python
openbacktesting.indicators.types.IndicatorHandle.df(self)
```

全部通道当前前缀的 pandas DataFrame 副本。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-dtype"></a>

### dtype

完整对象：`openbacktesting.indicators.types.IndicatorHandle.dtype`

```python
openbacktesting.indicators.types.IndicatorHandle.dtype(self)
```

底层只读数值缓冲区的数据类型。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-first-ready"></a>

### first_ready

完整对象：`openbacktesting.indicators.types.IndicatorHandle.first_ready`

```python
openbacktesting.indicators.types.IndicatorHandle.first_ready(self)
```

返回必要输出最早就绪位置；从未就绪时为总长度，不控制回调。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-metadata"></a>

### metadata

完整对象：`openbacktesting.indicators.types.IndicatorHandle.metadata`

```python
openbacktesting.indicators.types.IndicatorHandle.metadata(self)
```

返回来源元数据的深拷贝，修改不影响登记结果。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-ndim"></a>

### ndim

完整对象：`openbacktesting.indicators.types.IndicatorHandle.ndim`

```python
openbacktesting.indicators.types.IndicatorHandle.ndim(self)
```

输出维数；单通道为 1，多通道为 2。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-ready"></a>

### ready

完整对象：`openbacktesting.indicators.types.IndicatorHandle.ready`

```python
openbacktesting.indicators.types.IndicatorHandle.ready(self)
```

当前前缀最低历史条件是否满足的只读掩码。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-ready-at"></a>

### ready_at

完整对象：`openbacktesting.indicators.types.IndicatorHandle.ready_at`

```python
openbacktesting.indicators.types.IndicatorHandle.ready_at(self, bar)
```

查询必要输出与最低历史条件的就绪状态；不控制策略回调。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-s"></a>

### s

完整对象：`openbacktesting.indicators.types.IndicatorHandle.s`

```python
openbacktesting.indicators.types.IndicatorHandle.s(self)
```

首通道当前前缀的 pandas Series 副本；保存后不随游标增长。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-shape"></a>

### shape

完整对象：`openbacktesting.indicators.types.IndicatorHandle.shape`

```python
openbacktesting.indicators.types.IndicatorHandle.shape(self)
```

当前可见前缀的形状；多输出的时间轴位于最后。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorhandle-valid"></a>

### valid

完整对象：`openbacktesting.indicators.types.IndicatorHandle.valid`

```python
openbacktesting.indicators.types.IndicatorHandle.valid(self)
```

当前前缀各通道的只读有效性掩码；False 不表示数值零。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorspec"></a>

## IndicatorSpec

完整对象：`openbacktesting.indicators.types.IndicatorSpec`

```python
openbacktesting.indicators.types.IndicatorSpec(id: 'str', source: 'str', category: 'str', inputs: 'tuple[str, ...]', outputs: 'tuple[str, ...]', parameters: 'tuple[tuple[str, Parameter], ...]' = (), version: 'str' = '1', status: 'str' = 'available', reason: 'str' = '', required: 'tuple[str, ...] | None' = None, fixed: 'tuple[tuple[str, object], ...]' = (), minimum: 'int' = 1, windows: 'tuple[str, ...]' = (), dtype: 'str' = 'float64', unit: 'str' = 'native', missing_policy: 'str' = 'native-v1', causal: 'bool' = True, aliases: 'tuple[tuple[str, str], ...]' = (), history_sum: 'tuple' = (), history_offset: 'int' = 0, kind: 'str' = 'indicator', input_args: 'tuple[str, ...]' = (), input_defaults: 'tuple[tuple[str, str], ...]' = (), default_backend: 'str' = 'pandas-ta-classic.native', validity: 'str' = 'current-inputs') -> None
```

已审核指标定义；字段含身份、输入/输出、参数域、后端、有效性与历史要求。

源码：`src/openbacktesting/indicators/types.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `id` | `str` |
| `source` | `str` |
| `category` | `str` |
| `inputs` | `tuple[str, ...]` |
| `outputs` | `tuple[str, ...]` |
| `parameters` | `tuple[tuple[str, Parameter], ...]` |
| `version` | `str` |
| `status` | `str` |
| `reason` | `str` |
| `required` | `tuple[str, ...] \| None` |
| `fixed` | `tuple[tuple[str, object], ...]` |
| `minimum` | `int` |
| `windows` | `tuple[str, ...]` |
| `dtype` | `str` |
| `unit` | `str` |
| `missing_policy` | `str` |
| `causal` | `bool` |
| `aliases` | `tuple[tuple[str, str], ...]` |
| `history_sum` | `tuple` |
| `history_offset` | `int` |
| `kind` | `str` |
| `input_args` | `tuple[str, ...]` |
| `input_defaults` | `tuple[tuple[str, str], ...]` |
| `default_backend` | `str` |
| `validity` | `str` |

<a id="openbacktesting-indicators-types-indicatorspec-history-required"></a>

### history_required

完整对象：`openbacktesting.indicators.types.IndicatorSpec.history_required`

```python
openbacktesting.indicators.types.IndicatorSpec.history_required(self, parameters)
```

根据规范化 parameters 计算最低历史长度；不代表每个输出已经有效。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-indicatorspec-normalize"></a>

### normalize

完整对象：`openbacktesting.indicators.types.IndicatorSpec.normalize`

```python
openbacktesting.indicators.types.IndicatorSpec.normalize(self, parameters)
```

校验 parameters 映射，填充目录默认值并验证参数关系；非法值抛 IndicatorError。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-types-parameter"></a>

## Parameter

完整对象：`openbacktesting.indicators.types.Parameter`

```python
openbacktesting.indicators.types.Parameter(default: 'object', kind: 'str', minimum: 'float | None' = None, maximum: 'float | None' = None, choices: 'tuple' = ()) -> None
```

指标参数定义：default/kind 为默认值与类型，minimum/maximum/choices 限定允许值。

源码：`src/openbacktesting/indicators/types.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `default` | `object` |
| `kind` | `str` |
| `minimum` | `float \| None` |
| `maximum` | `float \| None` |
| `choices` | `tuple` |

<a id="openbacktesting-indicators-types-parameter-normalize"></a>

### normalize

完整对象：`openbacktesting.indicators.types.Parameter.normalize`

```python
openbacktesting.indicators.types.Parameter.normalize(self, value, indicator, name)
```

校验 value 的类型、边界和 choices 并转换为原生类型；失败抛 IndicatorError，indicator/name 用于定位。

源码：`src/openbacktesting/indicators/types.py`。

<a id="openbacktesting-indicators-methods-technicalanalysis-is-cross"></a>

## is_cross

完整对象：`openbacktesting.indicators.methods.TechnicalAnalysis.is_cross`

```python
openbacktesting.indicators.methods.TechnicalAnalysis.is_cross(self, left: collections.abc.Sequence[float] | numpy.ndarray | pandas.Series | openbacktesting.indicators.types.IndicatorHandle | float, right: collections.abc.Sequence[float] | numpy.ndarray | pandas.Series | openbacktesting.indicators.types.IndicatorHandle | float) -> bool
```

判断当前可见的最后一根是否发生任一方向交叉。

Args:
    left: 单通道句柄、数值序列或数字常量；不接受列名字符串。
    right: 单通道句柄、数值序列或数字常量；常量视为固定阈值。

Returns:
    Python bool。前一根允许相等，当前相等不算交叉。
    不足两根或最后两根含 NaN/无穷值时为 False。
    在 next 调用只读取输入当前前缀，不登记指标或影响预热。

源码：`src/openbacktesting/indicators/predicates.py`。

<a id="openbacktesting-indicators-methods-technicalanalysis-is-crossover"></a>

## is_crossover

完整对象：`openbacktesting.indicators.methods.TechnicalAnalysis.is_crossover`

```python
openbacktesting.indicators.methods.TechnicalAnalysis.is_crossover(self, left: collections.abc.Sequence[float] | numpy.ndarray | pandas.Series | openbacktesting.indicators.types.IndicatorHandle | float, right: collections.abc.Sequence[float] | numpy.ndarray | pandas.Series | openbacktesting.indicators.types.IndicatorHandle | float) -> bool
```

判断当前左值是否严格高于右值，且前一根左值小于等于右值。

Args:
    left: 单通道句柄、数值序列或数字常量；不接受列名字符串。
    right: 单通道句柄、数值序列或数字常量；常量视为固定阈值。

Returns:
    Python bool。只读取最后两根；不足两根或含 NaN/无穷值时为 False。
    有效位置与 ta.crossover 序列一致；不登记指标，可在 next 调用。

源码：`src/openbacktesting/indicators/predicates.py`。

<a id="openbacktesting-indicators-methods-technicalanalysis-is-crossunder"></a>

## is_crossunder

完整对象：`openbacktesting.indicators.methods.TechnicalAnalysis.is_crossunder`

```python
openbacktesting.indicators.methods.TechnicalAnalysis.is_crossunder(self, left: collections.abc.Sequence[float] | numpy.ndarray | pandas.Series | openbacktesting.indicators.types.IndicatorHandle | float, right: collections.abc.Sequence[float] | numpy.ndarray | pandas.Series | openbacktesting.indicators.types.IndicatorHandle | float) -> bool
```

判断当前左值是否严格低于右值，且前一根左值大于等于右值。

Args:
    left: 单通道句柄、数值序列或数字常量；不接受列名字符串。
    right: 单通道句柄、数值序列或数字常量；常量视为固定阈值。

Returns:
    Python bool。只读取最后两根；不足两根或含 NaN/无穷值时为 False。
    有效位置与 ta.crossunder 序列一致；不登记指标，可在 next 调用。

源码：`src/openbacktesting/indicators/predicates.py`。
