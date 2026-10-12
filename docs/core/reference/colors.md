# 颜色值与预设

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

颜色值提供构造、分量读取与透明度替换；颜色参数在策略内为 Color，配置和绘图导出为字符串。

[使用指南](../guides/plotting.md#颜色值与字符串) · [兼容与内部入口](classification.md)

<a id="openbacktesting-color"></a>

## Color

完整对象：`openbacktesting.Color`

```python
openbacktesting.Color(red: 'int', green: 'int', blue: 'int', alpha: 'int' = 255) -> None
```

按四通道比较的不可变颜色；alpha 表示不透明度，不与字符串隐式相等。

Args:
    red: 0–255 的原生 Python int 红色分量。
    green: 0–255 的原生 Python int 绿色分量。
    blue: 0–255 的原生 Python int 蓝色分量。
    alpha: 0–255 的原生 Python int；0 全透明，255 不透明。

Raises:
    TypeError: 通道不是原生 int，包括 bool。
    ValueError: 通道超出范围。

源码：`src/openbacktesting/colors.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `red` | `int` |
| `green` | `int` |
| `blue` | `int` |
| `alpha` | `int` |

<a id="openbacktesting-color-red"></a>

### red

完整对象：`openbacktesting.Color.red`

<a id="openbacktesting-color-green"></a>

### green

完整对象：`openbacktesting.Color.green`

<a id="openbacktesting-color-blue"></a>

### blue

完整对象：`openbacktesting.Color.blue`

<a id="openbacktesting-color-alpha"></a>

### alpha

完整对象：`openbacktesting.Color.alpha`

<a id="openbacktesting-color-transparency"></a>

### transparency

完整对象：`openbacktesting.Color.transparency`

```python
openbacktesting.Color.transparency(self) -> 'float'
```

由已量化 alpha 反算的 0–100 透明度，可能不等于原始百分比。

源码：`src/openbacktesting/colors.py`。

<a id="openbacktesting-color-from-hex"></a>

### from_hex

完整对象：`openbacktesting.Color.from_hex`

```python
openbacktesting.Color.from_hex(cls, value: 'str') -> 'Color'
```

解析六/八位十六进制颜色，六位补 FF。

Args:
    value: 不带空白的 #RRGGBB 或 #RRGGBBAA，大小写均可。

Returns:
    对应颜色值。

Raises:
    TypeError: 输入不是原生字符串。
    ValueError: 字符串格式非法；不接受 CSS 名称或短写。

源码：`src/openbacktesting/colors.py`。

<a id="openbacktesting-color-rgb"></a>

### rgb

完整对象：`openbacktesting.Color.rgb`

```python
openbacktesting.Color.rgb(cls, red: 'int', green: 'int', blue: 'int', *, transparency: 'float' = 0) -> 'Color'
```

以整数 RGB 和 0–100 透明度构造；0 不透明，100 全透明。

透明度仅接受原生有限 int/float，错误类型抛 TypeError，越界抛 ValueError。
alpha 按最接近字节量化，半值向上，不先舍入百分比。

源码：`src/openbacktesting/colors.py`。

<a id="openbacktesting-color-with-transparency"></a>

### with_transparency

完整对象：`openbacktesting.Color.with_transparency`

```python
openbacktesting.Color.with_transparency(self, transparency: 'float') -> 'Color'
```

以 0–100 透明度替换 alpha 并返回新值，不修改原色、不叠乘。

透明度与 rgb 使用相同范围、量化和异常契约。

源码：`src/openbacktesting/colors.py`。

<a id="openbacktesting-color-to-hex"></a>

### to_hex

完整对象：`openbacktesting.Color.to_hex`

```python
openbacktesting.Color.to_hex(self) -> 'str'
```

返回大写 #RRGGBBAA；全透明颜色仍保留 RGB，不转换为 None。

源码：`src/openbacktesting/colors.py`。

<a id="openbacktesting-color-from-gradient"></a>

### from_gradient

完整对象：`openbacktesting.Color.from_gradient`

```python
openbacktesting.Color.from_gradient(cls, value: 'float', *, lower: 'float', upper: 'float', lower_color: 'Color', upper_color: 'Color') -> 'Color'
```

标量在两端未预乘 RGBA 字节之间线性插值，区间外钳制到端点。

Args:
    value: 有限原生 int/float，不接受 bool。
    lower: 有限下界，必须小于 upper。
    upper: 有限上界。
    lower_color: 下界 Color，不接受 None 或字符串。
    upper_color: 上界 Color。

Returns:
    不可变 Color，各通道半字节向上量化；不修改两端颜色。

Raises:
    TypeError: 数值或颜色类型非法。
    ValueError: 非有限值或上下界顺序非法。

源码：`src/openbacktesting/colors.py`。

<a id="openbacktesting-colors-aqua"></a>

## AQUA

`openbacktesting.colors.AQUA` = `#00BCD4FF`。

<a id="openbacktesting-colors-black"></a>

## BLACK

`openbacktesting.colors.BLACK` = `#363A45FF`。

<a id="openbacktesting-colors-blue"></a>

## BLUE

`openbacktesting.colors.BLUE` = `#2196F3FF`。

<a id="openbacktesting-colors-fuchsia"></a>

## FUCHSIA

`openbacktesting.colors.FUCHSIA` = `#E040FBFF`。

<a id="openbacktesting-colors-gray"></a>

## GRAY

`openbacktesting.colors.GRAY` = `#787B86FF`。

<a id="openbacktesting-colors-green"></a>

## GREEN

`openbacktesting.colors.GREEN` = `#4CAF50FF`。

<a id="openbacktesting-colors-lime"></a>

## LIME

`openbacktesting.colors.LIME` = `#00E676FF`。

<a id="openbacktesting-colors-maroon"></a>

## MAROON

`openbacktesting.colors.MAROON` = `#880E4FFF`。

<a id="openbacktesting-colors-navy"></a>

## NAVY

`openbacktesting.colors.NAVY` = `#311B92FF`。

<a id="openbacktesting-colors-olive"></a>

## OLIVE

`openbacktesting.colors.OLIVE` = `#808000FF`。

<a id="openbacktesting-colors-orange"></a>

## ORANGE

`openbacktesting.colors.ORANGE` = `#FF9800FF`。

<a id="openbacktesting-colors-purple"></a>

## PURPLE

`openbacktesting.colors.PURPLE` = `#9C27B0FF`。

<a id="openbacktesting-colors-red"></a>

## RED

`openbacktesting.colors.RED` = `#F23645FF`。

<a id="openbacktesting-colors-silver"></a>

## SILVER

`openbacktesting.colors.SILVER` = `#B2B5BEFF`。

<a id="openbacktesting-colors-teal"></a>

## TEAL

`openbacktesting.colors.TEAL` = `#089981FF`。

<a id="openbacktesting-colors-white"></a>

## WHITE

`openbacktesting.colors.WHITE` = `#FFFFFFFF`。

<a id="openbacktesting-colors-yellow"></a>

## YELLOW

`openbacktesting.colors.YELLOW` = `#FDD835FF`。
