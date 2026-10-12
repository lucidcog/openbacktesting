# 声明绘图与导出

`Strategy.plotting` 生成独立绘图数据，`export_result(result)` 导出冻结的 `PlottingResult`。内核不渲染、不写图表文件，也不启动浏览器。桌面 Worker 执行和前端渲染仍未接入。

## 作者如何调用

在 `init` 创建面板，并用行情或指标句柄声明图层，在 `next/on_order/on_fill` 添加运行标记。下面的受测作者示例覆盖主图均线、副图 MACD、柱图、水平线、填充、静态颜色、逐 bar 背景/K 线颜色和行情/指标句柄：

[完整源码](../../../examples/strategies/plotting.py)

所有声明的 `id`、`title` 都可省略；可选 `pane` 默认主图，与此前调用无关。`pane()` 显式创建独立副图，返回 `PaneRef`；复用同一引用就共享面板及自动纵轴，字符串不能代替引用。

省略 ID 时按运行、引用类型及声明顺序生成 `auto:类型:序号`；相同调用顺序不受采集开关影响。省略标题时使用最终 ID，显式空标题保留为空，相同标题允许重复。空 ID、重复 ID、`main` 和 `auto:` 前缀作为显式 ID 会被拒绝。来源身份由引擎内部生成；跨运行或伪造引用无效。

## 数据来源与图层

| 调用                 | 含义与约束                                              |
| -------------------- | ------------------------------------------------------- |
| `line(handle)`       | 完整单通道行情或指标；默认折线，`style="step"` 为阶梯线 |
| `histogram(source)`  | 柱图，有限 `baseline=0` 参与自动范围                    |
| `level(value)`       | 有限水平常量，不分配整条数值数组                        |
| `fill(lower, upper)` | 接受两个 PlotRef，继承同一面板/轴；单位和偏移必须兼容   |
| `marker(...)`        | 在运行回调添加一次标记，与真实成交独立                  |

多输出指标先选通道，例如 `macd.histogram`。句柄必须来自当前运行；时间切片缩短、反转或错位会报错。同一个句柄的多个图层共享一个来源。绘图不登记新的计算指标，不改变回调、缓存键或指标值。

数值图层只接受本次运行的完整单通道行情/指标句柄和静态颜色；不接受数组或 pandas Series 直接作为图层来源。实数零保留为零，NaN/Infinity 导出为 null 并记录原因；布尔值须由作者显式转成数值。标记允许在 next、成交和订单通知中添加（包括 terminal 通知）；`on_start/on_finish`、运行外和封闭后不允许添加。

静态颜色接受 Color 或六/八位十六进制字符串；省略颜色或传入 None 使用消费者调色板；数组、引用和回调不能作为颜色。`gap_policy="break"` 默认断开缺口，`"connect"` 允许连线；均不插值或改变来源。`offset_bars` 是显示偏移，原始数据、可见性和交易时序不变，越过历史轴的显示点由消费者裁剪。

标记形状为 `circle/square/triangle_up/triangle_down`，定位为 `above_bar/below_bar/price`，price 定位须提供有限价格。`anchor_bar` 可指向当前或过去的合法 bar，不能指向未来；`knownAtBar` 固定记录产生时刻，不能由作者覆盖。文本按纯文本展示，消费者不可当作 HTML 执行。

## 颜色值与字符串

从包根导入 `Color, colors`。`colors.RED` 等 17 个预设已经是 Color；也可用 `Color.from_hex("#22aa44")`、`Color.rgb(34, 170, 68, transparency=40)` 或 `Color(34, 170, 68, alpha=153)` 构造。预设固定为已核对的 Pine v6 色值，例如 BLACK 为 `#363A45FF`，不随主题变化；全部预设见[颜色 API](../reference/colors.md)。

Color 不可变，按 RGBA 比较且可 hash/pickle，不与字符串隐式相等。`red/green/blue/alpha` 为只读整数。`with_transparency(40)` 返回新值、替换透明度且不修改原值；透明度 0 不透明、100 全透明，与 alpha 的方向相反。透明度只量化一次：`floor(255 * (100 - t) / 100 + 0.5)`；50 得到 alpha=128，反算 `transparency` 约为 49.8039，并不保留原始百分比。

通道仅接受 0–255 原生 int；透明度接受 0–100 原生有限 int/float，均拒绝 bool，NumPy 标量须显式转换。非法类型抛 TypeError，超界或格式错误抛 ValueError；进入 inputs/plotting 时包装为相应 InputError/PlottingError。字符串只支持六/八位十六进制，不接受 CSS 名称、短写、空白或换行。

所有绘图颜色入口统一输出大写八位 `#RRGGBBAA`，六位补 FF，`to_hex()` 和 `str(color)` 使用相同格式。既有小写绘图字符串的输出文本及载荷哈希会变化，但 RGBA 不变；读端仍接受历史大小写。不要对 Color 直接进行 JSON 编码，参数快照和绘图导出已完成转换。静态颜色在 init 声明；逐 bar 动态颜色在 next 计算，不接受 Color 数组或颜色指标句柄。

## 当根背景与 K 线着色

`bg_color(color, *, pane=None)` 设置主图或已有副图的当根背景，`bar_color(color)` 设置主图原始 K 线颜色；二者仅在 `next()` 及其同步分支、循环、辅助函数中可调用，返回 None。`init/on_start/on_finish/on_order/on_fill`、终末通知及运行结束后均拒绝。颜色为必填 Color、`#RRGGBB`、`#RRGGBBAA` 或 None，不接受数组、句柄、回调、CSS 或省略值。

同一 `(种类, 面板, bar)` 最后一次写入胜出。None 显式撤销该键覆盖；没有再次调用则保留当根较早写入，新 bar 不继承。alpha 为 `00` 的透明色仍是颜色，不等于清除。背景各面板独立，K 线颜色统一表达实体、影线和边框覆盖。颜色不影响行情或自动纵轴；背景仅覆盖当根横向槽位内、数据层下方的面板绘图区，不包含文字或坐标轴。

颜色调用不创建 source、plot、ID 或引用。首末根及指标无效期间都可在实际 `next()` 中写入颜色；破产、异常导致未调用 next 的 bar 和终止后区间不补色。持续状态由作者保存，并在每次实际 next 重发。这里的 Python 调用规则是本地契约，不是 Pine 的全局调用语法。

`colorEvents` 按调用顺序记录 `kind/pane/axis/anchorBar/knownAtBar/phase/sequence/color`，kind 为 `background/bar`，axis 为 `bars`，phase 为 `next`，两个 bar 位置相等。sequence 是本运行颜色域独立递增序号，不与 marker 或交易序号混排。显式清除输出 null。消费者回放先限制 knownAtBar，再按目标和 bar 取最后写入；没有事件不自动补色。

新结果始终包含 colorEvents；非空时 requiredFeatures 包含 `bar-coloring-v1`，仅清除事件也需要该能力。新协议消费者和快照导出保留 `1.0.0` 无颜色格式读取，新格式为 `1.1.0`；不承诺旧封闭 schema 可读新格式。不能完整支持颜色、alpha 和三部分 K 线覆盖的未来消费者必须拒绝该必需能力，不静默降级。本仓库目前只提供数据，没有实际渲染。

## 宿主如何导出

[完整源码](../../../examples/advanced/plotting_export.py)

成功结果在 `attrs["plotting_result"]` 保存不可变、可 pickle 的纯值元组快照，整个 attrs 仍可严格 JSON 编码。导出不读取 `_strategy`，不再次执行用户代码；修改返回字典、原生交易表或后续运行都不会影响旧快照。失败运行不发布成功快照，并封闭引用。

新载荷版本为 `1.1.0`，包含 axes/panes/scales/sources/plots/fills/markers/colorEvents/market/tradingFacts/execution、能力与诊断。行情保留五列，成交与账户直接复制既有账本；最后 bar 的正常 `bar` 和期末 `terminal` 账户记录分别保留。用户信号与实际成交的 bar 不一定相同。

结果中的 `sources` 是内部生成的数值数据表，供图层引用，不是作者声明入口。数值和掩码按 bar 位置对齐。`samplingMode="offline"` 的完整指标可能覆盖提前终止之后的历史；标记只记录实际调用。`execution.processed/strategyNext` 分别说明处理和 next 调用，不能根据最终恢复的全量游标推断执行范围。

有时区索引用 UTC 纳秒整数字符串与原时区表示，无时区日期使用 `naive-datetime` 标签，普通标量索引使用 `ordinal` 标签；不会猜测 UTC 或补造 bar。大于 JavaScript 安全整数的整数值编码为十进制字符串；绘图消费者显示时自行决定精度损失，不得把时间转成浮点数再关联。

## 自动纵轴与协议边界

作者不创建 scale、不填写上下限。主图共享价格轴，每个副图独立自动轴。消费者按当前可见有效图层、OHLC 高低点、可见水平线和柱基线计算范围，排除 invalid、未 ready 和不可见图层；常数范围需要扩展，空态需要默认范围。内核不输出依赖视口的固定 min/max。

唯一跨语言模式为 `packages/protocol/schemas/plotting-result.schema.json`。协议包的 Python `validate_plotting_result` 与 TypeScript `validatePlottingResult` 校验字段、引用归属、掩码、时序及预算，返回未知 optionalFeatures 的降级诊断；未知 requiredFeatures 或未支持的版本会拒绝。独立 core 不依赖协议包。

该载荷不含 runId、文件路径或权限，不内联到 1 MiB 控制帧。未来宿主需另行绑定运行、持久化制品并接入前端；schema 存在不代表 `strategy.execute/chart.render` 已可用。

## 采集开关与资源预算

`Backtest(..., plotting=False)` 保留声明引用、身份、类型与阶段检查，不保留历史视觉载荷，也不提供可导出的快照。颜色入口仍逐次校验并消耗 events，重复颜色、透明色和 None 都计数，不按最终覆盖数去重。grid 和受支持的 SAMBO 候选自动采用此模式；仅最优参数重跑遵循用户设置。评分函数只能依赖计算结果。

`Backtest(..., plotting_limits=PlottingLimits(...))` 可调整正整数预算：

| 配置   |      默认值 | 计数规则                                                           |
| ------ | ----------: | ------------------------------------------------------------------ |
| panes  |          32 | 包含主图                                                           |
| plots  |         256 | 包含 fill                                                          |
| points |  10,000,000 | 每个唯一密集源的点数，加五列行情与两列执行掩码；同源图层不重复计数 |
| events |   1,000,000 | 每次颜色调用、标记、成交与账户记录合计                             |
| text   |   1,048,576 | 作者 ID、标题、单位及标记文本的 UTF-8 字节                         |
| bytes  | 268,435,456 | 紧凑 UTF-8 JSON 导出字节                                           |

超限抛出 `PlottingError`，code 为 `PlottingLimitExceeded`，不删点或静默截断。字节预算在显式导出检查，超限后原始交易结果仍可读取。其他稳定 code 包括 `invalid-phase`、`invalid-reference`、`duplicate-id`、`misaligned-source`、`missing-snapshot`、`unsupported-version`。

通过 `uv run --locked python -m pytest tests/test_plotting.py tests/test_bar_coloring.py` 验证绘图快照、导出、资源限制与着色边界。此次抽离不新增性能基准，也不声明跨硬件性能阈值。

## 标量渐变

`Color.from_gradient(value, lower=..., upper=..., lower_color=..., upper_color=...)` 在两个 Color 的未预乘 RGBA 字节之间线性插值，各通道半字节向上取整，越界钳制到端点，端点与结果均不可变。数值只接受有限原生 int/float（拒绝 bool），两界严格递增；端点不接受字符串或 None。指标标量先显式 `float(...)` 并检查 valid。透明通道也参与插值，这不等同于感知色彩空间或屏幕合成；返回色直接复用现有 line/bar_color/bg_color 用法和导出协议。见[可运行渐变示例](../../../examples/strategies/local_value_helpers.py)。
