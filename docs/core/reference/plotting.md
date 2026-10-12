# 绘图声明与导出

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

公开对象参考。

[使用指南](../index.md) · [兼容与内部入口](classification.md)

<a id="openbacktesting-plotting-plotting"></a>

## Plotting

完整对象：`openbacktesting.plotting.Plotting`

```python
openbacktesting.plotting.Plotting(index: 'pd.Index', cursor: 'IndicatorCursor', *, enabled: 'bool' = True, limits: 'PlottingLimits | None' = None)
```

通过 Strategy.plotting 访问；init 声明行情/指标图层，next/on_order/on_fill 添加标记。

声明及标记的 id/title 可省略，title 默认使用最终 id；pane 默认主图。
bg_color/bar_color 仅在 next 写入当根颜色，不创建身份、不跨 bar 继承。
引用仅属于本次运行。纵轴自动适配，由消费者按可见有效数据计算范围。

源码：`src/openbacktesting/plotting/collector.py`。

<a id="openbacktesting-plotting-plotting-fill"></a>

### fill

完整对象：`openbacktesting.plotting.Plotting.fill`

```python
openbacktesting.plotting.Plotting.fill(self, lower: 'PlotRef', upper: 'PlotRef', id: 'str | None' = None, title: 'str | None' = None, color: 'Color | str | None' = None, gap_policy: 'Gap' = 'break') -> 'FillRef'
```

填充两个图层之间的区域；端点必须具有相同面板、轴、偏移及兼容单位。

源码：`src/openbacktesting/plotting/collector.py`。

<a id="openbacktesting-plotting-plotting-histogram"></a>

### histogram

完整对象：`openbacktesting.plotting.Plotting.histogram`

```python
openbacktesting.plotting.Plotting.histogram(self, source: 'IndicatorHandle', id: 'str | None' = None, title: 'str | None' = None, pane: 'PaneRef | None' = None, color: 'Color | str | None' = None, baseline: 'float' = 0, gap_policy: 'Gap' = 'break', offset_bars: 'int' = 0) -> 'PlotRef'
```

声明柱图；有限 baseline 参与消费者自动纵轴范围计算。

源码：`src/openbacktesting/plotting/collector.py`。

<a id="openbacktesting-plotting-plotting-level"></a>

### level

完整对象：`openbacktesting.plotting.Plotting.level`

```python
openbacktesting.plotting.Plotting.level(self, value: 'float', id: 'str | None' = None, title: 'str | None' = None, pane: 'PaneRef | None' = None, color: 'Color | str | None' = None) -> 'PlotRef'
```

声明有限水平线，保存一个常量，不复制整条数组。

源码：`src/openbacktesting/plotting/collector.py`。

<a id="openbacktesting-plotting-plotting-line"></a>

### line

完整对象：`openbacktesting.plotting.Plotting.line`

```python
openbacktesting.plotting.Plotting.line(self, source: 'IndicatorHandle', id: 'str | None' = None, title: 'str | None' = None, pane: 'PaneRef | None' = None, color: 'Color | str | None' = None, style: "Literal['line', 'step']" = 'line', gap_policy: 'Gap' = 'break', offset_bars: 'int' = 0) -> 'PlotRef'
```

声明线或阶梯线，默认主图、断开缺口；偏移只影响显示。

源码：`src/openbacktesting/plotting/collector.py`。

<a id="openbacktesting-plotting-plotting-marker"></a>

### marker

完整对象：`openbacktesting.plotting.Plotting.marker`

```python
openbacktesting.plotting.Plotting.marker(self, id: 'str | None' = None, title: 'str | None' = None, pane: 'PaneRef | None' = None, *, position: "Literal['above_bar', 'below_bar', 'price']" = 'above_bar', price: 'float | None' = None, shape: "Literal['circle', 'square', 'triangle_up', 'triangle_down']" = 'circle', text: 'str' = '', color: 'Color | str | None' = None, anchor_bar: 'int | None' = None) -> 'MarkerRef'
```

记录运行标记；anchor_bar 可回标历史，knownAtBar 始终为当前 bar。

源码：`src/openbacktesting/plotting/collector.py`。

<a id="openbacktesting-plotting-plotting-pane"></a>

### pane

完整对象：`openbacktesting.plotting.Plotting.pane`

```python
openbacktesting.plotting.Plotting.pane(self, id: 'str | None' = None, title: 'str | None' = None) -> 'PaneRef'
```

在 init 创建独立副图；返回引用供后续图层共享自动纵轴。

源码：`src/openbacktesting/plotting/collector.py`。

<a id="openbacktesting-plotting-plotting-bg-color"></a>

### bg_color

完整对象：`openbacktesting.plotting.Plotting.bg_color`

```python
openbacktesting.plotting.Plotting.bg_color(self, color: 'Color | str | None', *, pane: 'PaneRef | None' = None) -> 'None'
```

仅在 next 为当前 bar 写入面板背景；同目标最后一次写入胜出。

Args:
    color: 必填 Color、#RRGGBB、#RRGGBBAA 或 None；None 清除当根覆盖，透明色原样保留。
    pane: 默认主图，或本运行创建的副图引用。

Raises:
    PlottingError: 阶段、颜色、面板归属非法，或超过共享事件预算。

不跨 bar 继承；关闭采集仍校验并计数，不保留历史。

源码：`src/openbacktesting/plotting/collector.py`。

<a id="openbacktesting-plotting-plotting-bar-color"></a>

### bar_color

完整对象：`openbacktesting.plotting.Plotting.bar_color`

```python
openbacktesting.plotting.Plotting.bar_color(self, color: 'Color | str | None') -> 'None'
```

仅在 next 为当前主图 K 线写色，统一表达实体、影线和边框覆盖。

Args:
    color: 必填 Color、#RRGGBB、#RRGGBBAA 或 None；None 清除当根覆盖，透明色原样保留。

Raises:
    PlottingError: 阶段或颜色非法，或超过共享事件预算。

同 bar 最后一次写入胜出，不跨 bar 继承；不改变行情或自动纵轴。

源码：`src/openbacktesting/plotting/collector.py`。

<a id="openbacktesting-plotting-export-result"></a>

## export_result

完整对象：`openbacktesting.plotting.export_result`

```python
openbacktesting.plotting.export_result(result: 'pd.Series') -> 'dict'
```

从成功回测的冻结快照返回独立 PlottingResult 字典，不读取策略实例。

Args:
    result: 开启采集的 Backtest.run 或 runtime.run 结果。

Returns:
    可经 json.dumps(..., allow_nan=False) 编码的独立字典。

Raises:
    PlottingError: 快照缺失、类型或版本不支持，或超过导出字节预算。

源码：`src/openbacktesting/plotting/encoding.py`。

<a id="openbacktesting-plotting-fillref"></a>

## FillRef

完整对象：`openbacktesting.plotting.FillRef`

```python
openbacktesting.plotting.FillRef(id: 'str', title: 'str', _owner: 'Any') -> None
```

两个兼容图层之间的填充身份。

源码：`src/openbacktesting/plotting/types.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `id` | `str` |
| `title` | `str` |

<a id="openbacktesting-plotting-markerref"></a>

## MarkerRef

完整对象：`openbacktesting.plotting.MarkerRef`

```python
openbacktesting.plotting.MarkerRef(id: 'str', title: 'str', _owner: 'Any') -> None
```

一次运行标记的身份。

源码：`src/openbacktesting/plotting/types.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `id` | `str` |
| `title` | `str` |

<a id="openbacktesting-plotting-paneref"></a>

## PaneRef

完整对象：`openbacktesting.plotting.PaneRef`

```python
openbacktesting.plotting.PaneRef(id: 'str', title: 'str', _owner: 'Any') -> None
```

当前运行的副图身份；仅将此引用传给 pane 参数。

源码：`src/openbacktesting/plotting/types.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `id` | `str` |
| `title` | `str` |

<a id="openbacktesting-plotting-plotref"></a>

## PlotRef

完整对象：`openbacktesting.plotting.PlotRef`

```python
openbacktesting.plotting.PlotRef(id: 'str', title: 'str', _owner: 'Any') -> None
```

线、柱或水平线的身份，可作为 fill 端点。

源码：`src/openbacktesting/plotting/types.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `id` | `str` |
| `title` | `str` |

<a id="openbacktesting-plotting-plottingerror"></a>

## PlottingError

完整对象：`openbacktesting.plotting.PlottingError`

```python
openbacktesting.plotting.PlottingError(code: 'str', detail: 'str')
```

绘图契约错误，code 为可供调用者分派的稳定类别。

源码：`src/openbacktesting/plotting/types.py`。

<a id="openbacktesting-plotting-plottinglimits"></a>

## PlottingLimits

完整对象：`openbacktesting.plotting.PlottingLimits`

```python
openbacktesting.plotting.PlottingLimits(panes: 'int' = 32, plots: 'int' = 256, points: 'int' = 10000000, events: 'int' = 1000000, text: 'int' = 1048576, bytes: 'int' = 268435456) -> None
```

采集预算；所有上限均为正整数，bytes 在显式导出时检查。

points 按唯一密集源计数，包含五列行情与两列执行掩码。
panes 包含主图；plots 包含填充；events 包含每次颜色调用、标记和交易事实。
text 为作者身份、标题、单位及标记文本的累计 UTF-8 字节数。

源码：`src/openbacktesting/plotting/types.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `panes` | `int` |
| `plots` | `int` |
| `points` | `int` |
| `events` | `int` |
| `text` | `int` |
| `bytes` | `int` |

<a id="openbacktesting-plotting-plottinglimits-bytes"></a>

### bytes

完整对象：`openbacktesting.plotting.PlottingLimits.bytes`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-plotting-plottinglimits-events"></a>

### events

完整对象：`openbacktesting.plotting.PlottingLimits.events`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-plotting-plottinglimits-panes"></a>

### panes

完整对象：`openbacktesting.plotting.PlottingLimits.panes`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-plotting-plottinglimits-plots"></a>

### plots

完整对象：`openbacktesting.plotting.PlottingLimits.plots`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-plotting-plottinglimits-points"></a>

### points

完整对象：`openbacktesting.plotting.PlottingLimits.points`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-plotting-plottinglimits-text"></a>

### text

完整对象：`openbacktesting.plotting.PlottingLimits.text`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-plotting-paneref-id"></a>

## id 实例字段

id 为不可变身份信息，默认标题等于最终 ID；引用仅属于创建它的运行。

<a id="openbacktesting-plotting-paneref-title"></a>

## title 实例字段

title 为不可变身份信息，默认标题等于最终 ID；引用仅属于创建它的运行。

<a id="openbacktesting-plotting-plotref-id"></a>

## id 实例字段

id 为不可变身份信息，默认标题等于最终 ID；引用仅属于创建它的运行。

<a id="openbacktesting-plotting-plotref-title"></a>

## title 实例字段

title 为不可变身份信息，默认标题等于最终 ID；引用仅属于创建它的运行。

<a id="openbacktesting-plotting-fillref-id"></a>

## id 实例字段

id 为不可变身份信息，默认标题等于最终 ID；引用仅属于创建它的运行。

<a id="openbacktesting-plotting-fillref-title"></a>

## title 实例字段

title 为不可变身份信息，默认标题等于最终 ID；引用仅属于创建它的运行。

<a id="openbacktesting-plotting-markerref-id"></a>

## id 实例字段

id 为不可变身份信息，默认标题等于最终 ID；引用仅属于创建它的运行。

<a id="openbacktesting-plotting-markerref-title"></a>

## title 实例字段

title 为不可变身份信息，默认标题等于最终 ID；引用仅属于创建它的运行。

<a id="openbacktesting-plotting-plottingerror-code"></a>

## code 实例字段

稳定错误类别，详见绘图指南。
