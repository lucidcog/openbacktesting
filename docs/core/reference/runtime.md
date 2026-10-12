# 宿主运行入口

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

宿主发现本模块直接装饰的策略，注入图表数据、上下文与品种后执行；发现不依赖行情。

[使用指南](../guides/runtime.md) · [兼容与内部入口](classification.md)

<a id="openbacktesting-runtime-describe"></a>

## describe

完整对象：`openbacktesting.runtime.describe`

```python
openbacktesting.runtime.describe(namespace: collections.abc.Mapping) -> dict
```

无行情导出 inputs 及完整默认回测设置，不执行策略生命周期。

返回的 backtest 描述独立于 input schemaHash；修改副本不修改类声明。

源码：`src/openbacktesting/runtime.py`。

<a id="openbacktesting-runtime-run"></a>

## run

完整对象：`openbacktesting.runtime.run`

```python
openbacktesting.runtime.run(namespace: collections.abc.Mapping, request: collections.abc.Mapping | None = None, *, data: pandas.DataFrame, context: openbacktesting.data.context.DataContext, instrument: openbacktesting.broker.instrument.InstrumentSpec, settings: collections.abc.Mapping | None = None, options: collections.abc.Mapping | None = None, logs: openbacktesting.logs.RunLogs | None = None) -> pandas.Series
```

按本次图表运行新会话，返回既有结果及 backtest_snapshot。

Args:
    namespace: 宿主本次成功加载的模块；不再接受 bt-only 导出。
    request: 既有按标题的输入请求；None 使用默认参数。
    data: 当前图表 OHLC，必须具有带时区的 DatetimeIndex。
    context: 实际周期及图表、策略日历和统计共用的时区。
        在策略构造前转换内部索引，保留输入与绝对时刻，不触发重采样。
        改变时区需重新运行，当地时间条件及统计分日结果允许变化。
    instrument: 图表品种规格，不从行情推断。
    settings: 平铺设置的稀疏覆盖；枚举字段接受对应成员或精确字符串。
        切换类型必须同时给数值，default_qty_value=None 清除默认数量。
    options: 缓存预算、plotting 和 plotting_limits，属于宿主运行选项。
    logs: 可选的宿主日志会话，成功或异常后均可 get_logs，顺序重用清空旧记录。

不加载源码、不缓存旧实例、不修改声明；异常原样传播。

源码：`src/openbacktesting/runtime.py`。

<a id="openbacktesting-timeframeunit"></a>

## TimeframeUnit

完整对象：`openbacktesting.TimeframeUnit`

```python
openbacktesting.TimeframeUnit(*values)
```

时间 bar 单位；日历单位不隐式换算为固定秒数。

源码：`src/openbacktesting/data/timeframe.py`。

<a id="openbacktesting-timeframe"></a>

## Timeframe

完整对象：`openbacktesting.Timeframe`

```python
openbacktesting.Timeframe(unit: openbacktesting.data.timeframe.TimeframeUnit, multiplier: int) -> None
```

周期值；数据源支持范围由宿主验证，不承诺所有组合都有行情。

源码：`src/openbacktesting/data/timeframe.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `unit` | `<enum 'TimeframeUnit'>` |
| `multiplier` | `<class 'int'>` |

<a id="openbacktesting-timeframe-seconds"></a>

### seconds

完整对象：`openbacktesting.Timeframe.seconds`

```python
openbacktesting.Timeframe.seconds(cls, value: int) -> 'Timeframe'
```

创建秒周期。

源码：`src/openbacktesting/data/timeframe.py`。

<a id="openbacktesting-timeframe-snapshot"></a>

### snapshot

完整对象：`openbacktesting.Timeframe.snapshot`

```python
openbacktesting.Timeframe.snapshot(self) -> dict
```

返回独立的 unit/multiplier 纯值。

源码：`src/openbacktesting/data/timeframe.py`。

<a id="openbacktesting-timeframe-hours"></a>

### hours

完整对象：`openbacktesting.Timeframe.hours`

```python
openbacktesting.Timeframe.hours(cls, value: int) -> 'Timeframe'
```

小时规范化为分钟；24 小时不等于日线。

源码：`src/openbacktesting/data/timeframe.py`。

<a id="openbacktesting-timeframe-days"></a>

### days

完整对象：`openbacktesting.Timeframe.days`

```python
openbacktesting.Timeframe.days(cls, value: int) -> 'Timeframe'
```

创建日历日周期。

源码：`src/openbacktesting/data/timeframe.py`。

<a id="openbacktesting-timeframe-minutes"></a>

### minutes

完整对象：`openbacktesting.Timeframe.minutes`

```python
openbacktesting.Timeframe.minutes(cls, value: int) -> 'Timeframe'
```

创建分钟周期。

源码：`src/openbacktesting/data/timeframe.py`。

<a id="openbacktesting-timeframe-weeks"></a>

### weeks

完整对象：`openbacktesting.Timeframe.weeks`

```python
openbacktesting.Timeframe.weeks(cls, value: int) -> 'Timeframe'
```

创建日历周周期。

源码：`src/openbacktesting/data/timeframe.py`。

<a id="openbacktesting-timeframe-months"></a>

### months

完整对象：`openbacktesting.Timeframe.months`

```python
openbacktesting.Timeframe.months(cls, value: int) -> 'Timeframe'
```

创建日历月周期。

源码：`src/openbacktesting/data/timeframe.py`。

<a id="openbacktesting-datacontext"></a>

## DataContext

完整对象：`openbacktesting.DataContext`

```python
openbacktesting.DataContext(timeframe: openbacktesting.data.timeframe.Timeframe, timezone: str) -> None
```

描述已有行情的周期及图表、策略日历和统计共用的时区。

带时区行情在策略构造前转换为此时区；绝对时刻与原始数据不变。
统计按当地日界分组，切换时区后须重新运行，年化指标允许不同。
不提供下载、重采样或交易所日历能力。

源码：`src/openbacktesting/data/context.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `timeframe` | `<class 'openbacktesting.data.timeframe.Timeframe'>` |
| `timezone` | `<class 'str'>` |

<a id="openbacktesting-datacontext-snapshot"></a>

### snapshot

完整对象：`openbacktesting.DataContext.snapshot`

```python
openbacktesting.DataContext.snapshot(self) -> dict
```

返回独立纯值，不复用可变请求对象。

源码：`src/openbacktesting/data/context.py`。

<a id="openbacktesting-runtime-discover"></a>

## discover

完整对象：`openbacktesting.runtime.discover`

```python
openbacktesting.runtime.discover(namespace: collections.abc.Mapping) -> type[openbacktesting.engine.Strategy]
```

发现本模块直接装饰的唯一具体策略；别名去重，排除导入与继承入口。

Args:
    namespace: 成功加载模块的命名空间，必须含非空字符串 __name__。

Returns:
    type[Strategy]: 原策略类，不构造实例。

Raises:
    TypeError: 命名空间或声明无效。
    ValueError: 没有或存在多个入口。

源码：`src/openbacktesting/runtime.py`。

<a id="openbacktesting-defaultordersize"></a>

## DefaultOrderSize

完整对象：`openbacktesting.DefaultOrderSize`

```python
openbacktesting.DefaultOrderSize(mode: str, value: float) -> None
```

普通下单省略 qty 时的请求预算；不代表目标仓位或成交金额。

源码：`src/openbacktesting/simulation/config.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `mode` | `<class 'str'>` |
| `value` | `<class 'float'>` |

<a id="openbacktesting-defaultordersize-snapshot"></a>

### snapshot

完整对象：`openbacktesting.DefaultOrderSize.snapshot`

```python
openbacktesting.DefaultOrderSize.snapshot(self) -> dict
```

导出独立的模式和值。

源码：`src/openbacktesting/simulation/config.py`。

<a id="openbacktesting-defaultordersize-from-snapshot"></a>

### from_snapshot

完整对象：`openbacktesting.DefaultOrderSize.from_snapshot`

```python
openbacktesting.DefaultOrderSize.from_snapshot(cls, value: collections.abc.Mapping) -> 'DefaultOrderSize'
```

严格恢复完整配置，不填补缺失字段。

源码：`src/openbacktesting/simulation/config.py`。

<a id="openbacktesting-runlogs"></a>

## RunLogs

完整对象：`openbacktesting.RunLogs`

```python
openbacktesting.RunLogs()
```

宿主持有的单次运行日志，通过 runtime.run(..., logs=session) 注入。

顺序重用会在策略发现前清空记录；同一会话不能同时用于多个运行。
成功或异常退出后均可查询，返回列表和字典副本，不持有作者栈帧。

源码：`src/openbacktesting/logs.py`。

<a id="openbacktesting-runlogs-get-logs"></a>

### get_logs

完整对象：`openbacktesting.RunLogs.get_logs`

```python
openbacktesting.RunLogs.get_logs(self) -> list[dict[str, str | int | None]]
```

返回本次运行全部日志的独立副本；首次运行前为空列表。

源码：`src/openbacktesting/logs.py`。

<a id="openbacktesting-runtime-optimize"></a>

## optimize

完整对象：`openbacktesting.runtime.optimize`

```python
openbacktesting.runtime.optimize(namespace: collections.abc.Mapping, search: collections.abc.Mapping, *, path, identity, data: pandas.DataFrame, context: openbacktesting.data.context.DataContext, instrument: openbacktesting.broker.instrument.InstrumentSpec, request=None, settings=None, constraint=None, constraint_id=None, cancel=None, on_progress=None) -> openbacktesting.optimizer.query.ExperimentResult
```

串行穷举选定 inputs，将每份完整 Portfolio 提交到新本地结果库。

未选值来自当前 request；仅保留 Portfolio，不采集日志/绘图。
identity 是宿主提供的 ExecutionIdentity；数据/配置身份由框架计算。
constraint 使用完整 wire 值并需 constraint_id；cancel 为无参 callable。
返回只读 ExperimentResult；策略失败组记错误后继续，存储失败停止。

源码：`src/openbacktesting/runtime.py`。

<a id="openbacktesting-runtime-resume-optimization"></a>

## resume_optimization

完整对象：`openbacktesting.runtime.resume_optimization`

```python
openbacktesting.runtime.resume_optimization(namespace: collections.abc.Mapping, *, path, experiment_id: str, identity, data: pandas.DataFrame, context: openbacktesting.data.context.DataContext, instrument: openbacktesting.broker.instrument.InstrumentSpec, request=None, settings=None, constraint=None, constraint_id=None, cancel=None, on_progress=None) -> openbacktesting.optimizer.query.ExperimentResult
```

核验当前声明、输入与执行身份后恢复未完成试验；不自动重试失败组。

源码：`src/openbacktesting/runtime.py`。
