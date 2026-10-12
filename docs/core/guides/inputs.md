# 参数声明与配置

## 用户脚本：声明 Input

策略可以在类字段声明可配置参数。`title` 必填且在同一策略内唯一，包括不同分组与继承字段；它同时是显示名称和配置键，不需要额外 `id`。字段名只负责 Python 代码中的访问。

```python
from openbacktesting import Strategy, backtest, inputs


@backtest(commission_value=0.2, exclusive_orders=True)
class ConfigurableSma(Strategy):
    length = inputs.int(20, minval=1, title="均线周期", group="均线")

    def init(self):
        self.line = self.ta.sma(length=self.length)

    def next(self):
        pass

```

用户不需要写 schema、request、`inputs.describe()`、`bt.run()` 或 `bt.run_inputs()`。全部九种参数的声明与实际读取见 [完整 Input 示例](../../../examples/strategies/all_inputs.py)；带参数双 EMA 策略见 [内置 EMA 参数示例](../../../examples/strategies/ema_inputs.py)。两者都只声明策略与默认回测设置，策略内通过 `self.length` 读取本次解析后的值。

| 声明             | 运行值与配置表示                     | 约束                                                        |
| ---------------- | ------------------------------------ | ----------------------------------------------------------- |
| `inputs.bool`    | bool                                 | 拒绝数字、字符串强转                                        |
| `inputs.int`     | int                                  | 支持 options 或 minval/maxval/step；不接受 bool 或浮点      |
| `inputs.float`   | float                                | 同上；有限整数可无损转换，拒绝 NaN/Infinity                 |
| `inputs.price`   | float                                | 保留价格种类；允许负值，不接受数值边界/options              |
| `inputs.string`  | str                                  | 支持 options，保留原字符串空白                              |
| `inputs.time`    | Unix 毫秒整数                        | 不猜测时间单位；int/time 范围为 `±(2^53−1)`                 |
| `inputs.session` | 规范化时段字符串                     | 支持跨午夜、多区间、星期后缀、24x7；不自动过滤行情          |
| `inputs.color`   | 运行值为 `Color`，配置为 `#RRGGBBAA` | 默认值/原生覆盖接受 Color 或六/八位字符串；统一大写八位编码 |
| `inputs.enum`    | Python Enum 成员；配置保存成员名称   | 默认成员确定枚举类型，支持 options；拒绝别名和异类成员      |

颜色 Input 已统一返回 `Color`：`inputs.color("#22aa44", title="上涨颜色")` 与 `inputs.color(colors.TEAL, title="上涨颜色")` 都可声明，先从包根导入 `colors`。策略中直接使用 `self.up_color.with_transparency(85)` 得到派生色，传给绘图无需转换；Input 自身仍只读。需要文本时显式调用 `to_hex()`，不再对运行值进行字符串切片或比较。

`bt.run(up_color=...)` 接受 Color 或字符串；`run_inputs` 标题请求只接受字符串，拒绝 Color、None 和对象映射。发现声明、参数快照和 schemaHash 仍使用规范化字符串，等价六位/八位/Color 默认值产生相同摘要。grid 候选规范化为 Color 后传入 constraint 和原生 heatmap 标签，配置及结果快照仍为字符串。

完整用法见[绘图与颜色示例](plotting.md)、[颜色 API](../reference/colors.md)。当前支持 core 参数声明与注入，不包含桌面颜色选择器。

例如 `inputs.enum(Mode.FAST, title="模式", options=[Mode.FAST, Mode.SLOW])` 的配置值是 `"FAST"` 或 `"SLOW"`，原生 Python 运行值仍是 `Mode` 成员。枚举类型标识由类自动导出；跨进程使用可导入的模块顶层策略与枚举类。数值 options 与边界/step 互斥；step 仅表示调整增量，不是整除限制。时段 `24x7` 规范化为 `0000-0000:1234567`，省略星期表示每天；时区与交易日历由消费方另行解释。

公共提示支持 `tooltip/group/inline/display/active/confirm`。active 可为布尔常量或 `{"title": "某个布尔参数"}`；引用须有效且无环。禁用、display 隐藏或 confirm 提示不删除字段、不跳过验证，也不会启动界面。input 字段在运行期间只读，派生计算请使用普通局部变量或其他实例字段。

底层运行 API 供框架与原生 Python 调用方使用：`bt.run_inputs(request)` 按 title 关联，`bt.run(length=30)` 按字段名关联，使用同一校验规则；声明策略拒绝未声明属性。校验失败不构造策略或 broker，也不静默回落默认值。`inputs.InputError` 提供 `code/title/expected/actual_type`；标题入口接收映射对象，JSON 文本重复键需由调用方在解码时拒绝。

结果 `attrs["input_snapshot"]` 包含格式版本、声明摘要、core 版本、所有有效值和显式覆盖标题；统计索引保持不变。仅改标题、字段或说明文字也会改变声明摘要，旧请求须重新发现并确认；标题改名不得按旧字段自动迁移。快照不是代码、数据或依赖的完整项目快照。

声明策略支持 `grid` 优化，候选按 Python 字段名传入，所有候选在 constraint、采样及派发前校验。首期明确拒绝声明策略的 `sambo/skopt`，未使用 input 声明的旧策略保持原有参数与优化行为。分数回测的标题入口继续经过原生单位转换。
