# 参数声明与解析

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

在策略类中声明参数，再按唯一 title 发现和注入值；定义、解析与运行时值分开管理。

[使用指南](../guides/inputs.md) · [兼容与内部入口](classification.md)

<a id="openbacktesting-inputs-inputerror"></a>

## InputError

完整对象：`openbacktesting.inputs.InputError`

```python
openbacktesting.inputs.InputError(code, title, expected, value=None)
```

可由调用方按 code/title/expected/actual_type 展示的参数错误。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-inputspec"></a>

## InputSpec

完整对象：`openbacktesting.inputs.InputSpec`

```python
openbacktesting.inputs.InputSpec(kind: 'str', title: 'str', default: 'object', options: 'tuple | None' = None, bounds: 'tuple' = (), metadata: 'tuple' = (), enum_type: 'type[Enum] | None' = None, bindings: 'tuple' = ()) -> None
```

策略类字段的不可变声明；通过 inputs 工厂创建，实例读取本次运行值。

源码：`src/openbacktesting/strategy/inputs.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `kind` | `str` |
| `title` | `str` |
| `default` | `object` |
| `options` | `tuple \| None` |
| `bounds` | `tuple` |
| `metadata` | `tuple` |
| `enum_type` | `type[Enum] \| None` |
| `bindings` | `tuple` |

<a id="openbacktesting-inputs-inputspec-encode"></a>

### encode

完整对象：`openbacktesting.inputs.InputSpec.encode`

```python
openbacktesting.inputs.InputSpec.encode(self, value)
```

将已规范化 value 编码为配置表示；枚举使用成员名称，颜色使用大写八位字符串。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-inputspec-export"></a>

### export

完整对象：`openbacktesting.inputs.InputSpec.export`

```python
openbacktesting.inputs.InputSpec.export(self, attribute)
```

导出声明字典；attribute 是 Python 字段名，配置关联仍使用唯一 title。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-inputspec-normalize"></a>

### normalize

完整对象：`openbacktesting.inputs.InputSpec.normalize`

```python
openbacktesting.inputs.InputSpec.normalize(self, value, *, wire=False)
```

验证并规范化 value；wire=True 按序列化表示解析枚举，非法值抛 InputError。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-resolvedinputs"></a>

## ResolvedInputs

完整对象：`openbacktesting.inputs.ResolvedInputs`

```python
openbacktesting.inputs.ResolvedInputs(schema_hash: 'str', runtime: 'tuple', encoded: 'tuple', overridden: 'tuple', attributes: 'tuple') -> None
```

已校验的一次输入解析结果，包含声明摘要、运行值、编码值与显式覆盖标题。

源码：`src/openbacktesting/strategy/inputs.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `schema_hash` | `str` |
| `runtime` | `tuple` |
| `encoded` | `tuple` |
| `overridden` | `tuple` |
| `attributes` | `tuple` |

<a id="openbacktesting-inputs-resolvedinputs-overrides"></a>

### overrides

完整对象：`openbacktesting.inputs.ResolvedInputs.overrides`

```python
openbacktesting.inputs.ResolvedInputs.overrides(self)
```

返回显式覆盖的 Python 字段和值；供策略实例注入使用。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-resolvedinputs-snapshot"></a>

### snapshot

完整对象：`openbacktesting.inputs.ResolvedInputs.snapshot`

```python
openbacktesting.inputs.ResolvedInputs.snapshot(self)
```

返回用于结果 attrs 的版本、声明摘要、完整值和显式覆盖标题快照。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-schema-version"></a>

## SCHEMA_VERSION

参数发现与输入请求使用的 schema 版本。

`openbacktesting.inputs.SCHEMA_VERSION` = `1.0.0`。

<a id="openbacktesting-inputs-bool"></a>

## bool

完整对象：`openbacktesting.inputs.bool`

```python
openbacktesting.inputs.bool(kind, defval, *, title, tooltip='', group='', inline='', display=None, active=True, confirm=False, options=<object object>, minval=<object object>, maxval=<object object>, step=<object object>)
```

声明策略的只读配置字段；种类由 inputs.bool/int/float 等入口绑定。

Args:
    defval: 默认值，必须符合声明种类。
    title: 必填且在同一策略中唯一；同时是标题配置键。
    tooltip: 提示文本。
    group: 展示分组，不改变 title 的唯一性范围。
    inline: 同行展示提示。
    display: all/none/status_line/data_window，仅为元数据。
    active: 布尔常量或引用 bool 参数标题的映射，不跳过值验证。
    confirm: 确认提示元数据，不启动界面。
    options: 可选值集合；数值种类不可同时指定边界或 step。
    minval: 数值下界，仅用于 int/float。
    maxval: 数值上界，仅用于 int/float。
    step: 调整增量，不是整除限制，仅用于 int/float。

Returns:
    InputSpec: 类字段描述符；实例读取本次解析值。

Raises:
    InputError: 声明、默认值、参数域或展示元数据非法。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-color"></a>

## color

完整对象：`openbacktesting.inputs.color`

```python
openbacktesting.inputs.color(kind, defval, *, title, tooltip='', group='', inline='', display=None, active=True, confirm=False, options=<object object>, minval=<object object>, maxval=<object object>, step=<object object>)
```

声明策略的只读配置字段；种类由 inputs.bool/int/float 等入口绑定。

Args:
    defval: 默认值，必须符合声明种类。
    title: 必填且在同一策略中唯一；同时是标题配置键。
    tooltip: 提示文本。
    group: 展示分组，不改变 title 的唯一性范围。
    inline: 同行展示提示。
    display: all/none/status_line/data_window，仅为元数据。
    active: 布尔常量或引用 bool 参数标题的映射，不跳过值验证。
    confirm: 确认提示元数据，不启动界面。
    options: 可选值集合；数值种类不可同时指定边界或 step。
    minval: 数值下界，仅用于 int/float。
    maxval: 数值上界，仅用于 int/float。
    step: 调整增量，不是整除限制，仅用于 int/float。

Returns:
    InputSpec: 类字段描述符；实例读取本次解析值。

Raises:
    InputError: 声明、默认值、参数域或展示元数据非法。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-describe"></a>

## describe

完整对象：`openbacktesting.inputs.describe`

```python
openbacktesting.inputs.describe(strategy_class)
```

导出已加载策略类的独立 JSON 定义，不运行策略。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-enum"></a>

## enum

完整对象：`openbacktesting.inputs.enum`

```python
openbacktesting.inputs.enum(kind, defval, *, title, tooltip='', group='', inline='', display=None, active=True, confirm=False, options=<object object>, minval=<object object>, maxval=<object object>, step=<object object>)
```

声明策略的只读配置字段；种类由 inputs.bool/int/float 等入口绑定。

Args:
    defval: 默认值，必须符合声明种类。
    title: 必填且在同一策略中唯一；同时是标题配置键。
    tooltip: 提示文本。
    group: 展示分组，不改变 title 的唯一性范围。
    inline: 同行展示提示。
    display: all/none/status_line/data_window，仅为元数据。
    active: 布尔常量或引用 bool 参数标题的映射，不跳过值验证。
    confirm: 确认提示元数据，不启动界面。
    options: 可选值集合；数值种类不可同时指定边界或 step。
    minval: 数值下界，仅用于 int/float。
    maxval: 数值上界，仅用于 int/float。
    step: 调整增量，不是整除限制，仅用于 int/float。

Returns:
    InputSpec: 类字段描述符；实例读取本次解析值。

Raises:
    InputError: 声明、默认值、参数域或展示元数据非法。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-float"></a>

## float

完整对象：`openbacktesting.inputs.float`

```python
openbacktesting.inputs.float(kind, defval, *, title, tooltip='', group='', inline='', display=None, active=True, confirm=False, options=<object object>, minval=<object object>, maxval=<object object>, step=<object object>)
```

声明策略的只读配置字段；种类由 inputs.bool/int/float 等入口绑定。

Args:
    defval: 默认值，必须符合声明种类。
    title: 必填且在同一策略中唯一；同时是标题配置键。
    tooltip: 提示文本。
    group: 展示分组，不改变 title 的唯一性范围。
    inline: 同行展示提示。
    display: all/none/status_line/data_window，仅为元数据。
    active: 布尔常量或引用 bool 参数标题的映射，不跳过值验证。
    confirm: 确认提示元数据，不启动界面。
    options: 可选值集合；数值种类不可同时指定边界或 step。
    minval: 数值下界，仅用于 int/float。
    maxval: 数值上界，仅用于 int/float。
    step: 调整增量，不是整除限制，仅用于 int/float。

Returns:
    InputSpec: 类字段描述符；实例读取本次解析值。

Raises:
    InputError: 声明、默认值、参数域或展示元数据非法。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-int"></a>

## int

完整对象：`openbacktesting.inputs.int`

```python
openbacktesting.inputs.int(kind, defval, *, title, tooltip='', group='', inline='', display=None, active=True, confirm=False, options=<object object>, minval=<object object>, maxval=<object object>, step=<object object>)
```

声明策略的只读配置字段；种类由 inputs.bool/int/float 等入口绑定。

Args:
    defval: 默认值，必须符合声明种类。
    title: 必填且在同一策略中唯一；同时是标题配置键。
    tooltip: 提示文本。
    group: 展示分组，不改变 title 的唯一性范围。
    inline: 同行展示提示。
    display: all/none/status_line/data_window，仅为元数据。
    active: 布尔常量或引用 bool 参数标题的映射，不跳过值验证。
    confirm: 确认提示元数据，不启动界面。
    options: 可选值集合；数值种类不可同时指定边界或 step。
    minval: 数值下界，仅用于 int/float。
    maxval: 数值上界，仅用于 int/float。
    step: 调整增量，不是整除限制，仅用于 int/float。

Returns:
    InputSpec: 类字段描述符；实例读取本次解析值。

Raises:
    InputError: 声明、默认值、参数域或展示元数据非法。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-price"></a>

## price

完整对象：`openbacktesting.inputs.price`

```python
openbacktesting.inputs.price(kind, defval, *, title, tooltip='', group='', inline='', display=None, active=True, confirm=False, options=<object object>, minval=<object object>, maxval=<object object>, step=<object object>)
```

声明策略的只读配置字段；种类由 inputs.bool/int/float 等入口绑定。

Args:
    defval: 默认值，必须符合声明种类。
    title: 必填且在同一策略中唯一；同时是标题配置键。
    tooltip: 提示文本。
    group: 展示分组，不改变 title 的唯一性范围。
    inline: 同行展示提示。
    display: all/none/status_line/data_window，仅为元数据。
    active: 布尔常量或引用 bool 参数标题的映射，不跳过值验证。
    confirm: 确认提示元数据，不启动界面。
    options: 可选值集合；数值种类不可同时指定边界或 step。
    minval: 数值下界，仅用于 int/float。
    maxval: 数值上界，仅用于 int/float。
    step: 调整增量，不是整除限制，仅用于 int/float。

Returns:
    InputSpec: 类字段描述符；实例读取本次解析值。

Raises:
    InputError: 声明、默认值、参数域或展示元数据非法。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-request-for"></a>

## request_for

完整对象：`openbacktesting.inputs.request_for`

```python
openbacktesting.inputs.request_for(strategy_class, kwargs)
```

将有声明的 strategy_class 的 Python 字段 kwargs 转为标题请求；调用前须确认类包含 Input，非法值抛 InputError。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-resolve-native"></a>

## resolve_native

完整对象：`openbacktesting.inputs.resolve_native`

```python
openbacktesting.inputs.resolve_native(strategy_class, kwargs)
```

原生字段入口；无声明类返回 None 以保留旧行为。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-resolve-request"></a>

## resolve_request

完整对象：`openbacktesting.inputs.resolve_request`

```python
openbacktesting.inputs.resolve_request(strategy_class, request)
```

按 strategy_class 校验 request 的版本、摘要和标题值；失败抛 InputError，返回 ResolvedInputs。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-session"></a>

## session

完整对象：`openbacktesting.inputs.session`

```python
openbacktesting.inputs.session(kind, defval, *, title, tooltip='', group='', inline='', display=None, active=True, confirm=False, options=<object object>, minval=<object object>, maxval=<object object>, step=<object object>)
```

声明策略的只读配置字段；种类由 inputs.bool/int/float 等入口绑定。

Args:
    defval: 默认值，必须符合声明种类。
    title: 必填且在同一策略中唯一；同时是标题配置键。
    tooltip: 提示文本。
    group: 展示分组，不改变 title 的唯一性范围。
    inline: 同行展示提示。
    display: all/none/status_line/data_window，仅为元数据。
    active: 布尔常量或引用 bool 参数标题的映射，不跳过值验证。
    confirm: 确认提示元数据，不启动界面。
    options: 可选值集合；数值种类不可同时指定边界或 step。
    minval: 数值下界，仅用于 int/float。
    maxval: 数值上界，仅用于 int/float。
    step: 调整增量，不是整除限制，仅用于 int/float。

Returns:
    InputSpec: 类字段描述符；实例读取本次解析值。

Raises:
    InputError: 声明、默认值、参数域或展示元数据非法。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-string"></a>

## string

完整对象：`openbacktesting.inputs.string`

```python
openbacktesting.inputs.string(kind, defval, *, title, tooltip='', group='', inline='', display=None, active=True, confirm=False, options=<object object>, minval=<object object>, maxval=<object object>, step=<object object>)
```

声明策略的只读配置字段；种类由 inputs.bool/int/float 等入口绑定。

Args:
    defval: 默认值，必须符合声明种类。
    title: 必填且在同一策略中唯一；同时是标题配置键。
    tooltip: 提示文本。
    group: 展示分组，不改变 title 的唯一性范围。
    inline: 同行展示提示。
    display: all/none/status_line/data_window，仅为元数据。
    active: 布尔常量或引用 bool 参数标题的映射，不跳过值验证。
    confirm: 确认提示元数据，不启动界面。
    options: 可选值集合；数值种类不可同时指定边界或 step。
    minval: 数值下界，仅用于 int/float。
    maxval: 数值上界，仅用于 int/float。
    step: 调整增量，不是整除限制，仅用于 int/float。

Returns:
    InputSpec: 类字段描述符；实例读取本次解析值。

Raises:
    InputError: 声明、默认值、参数域或展示元数据非法。

源码：`src/openbacktesting/strategy/inputs.py`。

<a id="openbacktesting-inputs-time"></a>

## time

完整对象：`openbacktesting.inputs.time`

```python
openbacktesting.inputs.time(kind, defval, *, title, tooltip='', group='', inline='', display=None, active=True, confirm=False, options=<object object>, minval=<object object>, maxval=<object object>, step=<object object>)
```

声明策略的只读配置字段；种类由 inputs.bool/int/float 等入口绑定。

Args:
    defval: 默认值，必须符合声明种类。
    title: 必填且在同一策略中唯一；同时是标题配置键。
    tooltip: 提示文本。
    group: 展示分组，不改变 title 的唯一性范围。
    inline: 同行展示提示。
    display: all/none/status_line/data_window，仅为元数据。
    active: 布尔常量或引用 bool 参数标题的映射，不跳过值验证。
    confirm: 确认提示元数据，不启动界面。
    options: 可选值集合；数值种类不可同时指定边界或 step。
    minval: 数值下界，仅用于 int/float。
    maxval: 数值上界，仅用于 int/float。
    step: 调整增量，不是整除限制，仅用于 int/float。

Returns:
    InputSpec: 类字段描述符；实例读取本次解析值。

Raises:
    InputError: 声明、默认值、参数域或展示元数据非法。

源码：`src/openbacktesting/strategy/inputs.py`。
