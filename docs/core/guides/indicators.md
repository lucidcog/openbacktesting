# 指标使用契约与能力

内核基于固定的 `pandas-ta-classic==0.8.32` 提供自有指标目录、批量计算和策略登记。当前目录有 247 个分类入口：211 个普通指标、24 个工具与确认事件、9 种形态开放；另有 cdl_pattern、vp、tos_stdevall 三个入口不开放交易调用。计数来自实际制品，不以文档宣传的 224 为验收常量。

事实来源为[固定目录](../../../src/openbacktesting/indicators/catalog.json)、[逐入口合约测试](../../../tests/test_indicator_catalog.py)和子包实施记录。上游升级时必须重新审核清单、参数域、输出和因果性，不能自动反射开放新增函数。

下列片段说明局部调用；`frame` 是调用方准备的行情 DataFrame，策略方法片段须放入 Strategy 子类。完整可执行代码由[示例入口](../examples.md)提供。

## API 与后端边界

```python
from openbacktesting import indicators

result = indicators.compute("ta.ema", frame, parameters={"length": 20})
print(result.s)
print(indicators.describe("ta.macd").outputs)
```

策略内置指标统一通过 `self.ta` 调用，序列指标的方法签名、默认值和返回类型从审核目录生成并随 wheel 发布；即时交叉判断由独立实现提供：

```python
def init(self):
    self.ema = self.ta.ema(length=20)
    self.macd = self.ta.macd()
    self.smoothed = self.ta.ema(self.macd.histogram, length=5)

def next(self):
    average = self.ema[-1]
    histogram = self.macd.histogram[-1]
```

单输出保留 `IndicatorHandle`；多输出提供只读具名结果，通道视图在初始化时建立，重复属性读取不复制历史或重新登记。MACD 的 `line` 与规范名 `macd` 是同对象别名，`histogram`、`signal` 独立可读；BBands 为 `lower/middle/upper/bandwidth/percent`。多输出支持规范名键及 `ready/valid/metadata/df` 读取，不隐式选择主线进行算术或接受数值通道索引。

单输入首参 `source` 可用行情列名或同运行单通道，例如 `self.ta.ema("Open", length=20)`；省略或 `None` 使用默认行情。交叉可写 `self.ta.crossover(left, right)`，事件取值可写 `self.ta.valuewhen(condition, source, occurrence=0)`，参数接受行情列名或同运行单通道句柄；其他多输入使用 `inputs`；非空 `source` 与 `inputs` 同时指定会报错。不推断缺少的 benchmark 等非标准输入，不接受任意 ndarray 或跨运行句柄。`backend` 与 `required_outputs` 沿用原选项，必要输出始终使用规范名（MACD 主线为 `macd`）。

### 交叉序列与即时判断

| 入口                                                       | 返回                                      | 使用阶段与用途                                                                 |
| ---------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------ |
| `self.ta.cross/crossover/crossunder(left, right)`          | `IndicatorHandle`，有效值 0/1，无效值 NaN | init 登记，可继续组合或在 next 用 `[-1]` 读取                                  |
| `self.ta.is_cross/is_crossover/is_crossunder(left, right)` | Python `bool`                             | 直接判断输入当前可见的最后两根，适合 next 条件分支，不登记指标、不影响逐根回调 |

两组使用相同交叉规则：上穿为当前左值严格大于右值且前值小于等于；下穿反向；当前相等不算交叉。序列不足两根或参与比较的值无效时，`is_*` 返回 `False`，序列仍保留 NaN 与 `valid` 掩码。

`is_*` 接受单通道句柄、list/tuple、NumPy 数组、pandas Series 或数字阈值；Series 按位置取最近两项。句柄遵循可见游标和 `valid` 掩码；NaN/无穷值视为无效。传 `self.close` 而非列名字符串，多输出先选择通道。不接受 `inputs/backend/required_outputs`。传入独立数组时，调用方负责截断到当前时点；在 init 调用会判断完整输入的最后两根，不产生序列。

完整双入口用法见 [cross_signals.py](../../../examples/strategies/cross_signals.py)。

`ta` 是策略保留属性；同名类字段、方法、Input 字段、参数或实例赋值必须改名，Input 展示标题不受影响。所有方法仅能在 `init()` 登记。开发阶段运行 `uv run --locked python scripts/generate_indicator_api.py --check` 校验生成物；修改目录后运行 `uv run --locked python scripts/generate_indicator_api.py`，不手改生成的运行时文件。实现与验收见方法式接口记录。

内置指标在 `init()` 通过 `self.ta` 登记。`inputs` 映射只接受行情列名或本次运行的单通道句柄；`backend` 和 `required_outputs` 属于运行选项，其余参数按定义严格校验。未知参数、bool 充当整数、非有限数值和非法参数关系均被拒绝。上游未公开的 `**kwargs` 不透传。

后端由每项目录固定：既有封装为 `pandas-ta-classic.native`，显式传入 `talib=False`；新增本地公式与修订 NVI/PVI 为 `openbacktesting.numpy`，不安装 TA-Lib/Numba extras。测试在模拟 TA-Lib 已安装时阻止其导入；库的安装状态不改变内置调用。只有 SMA 另提供 `backend="pandas.sma"`，作为替换实现的契约证明。未知后端明确失败，没有回退。

指标领域位于 `indicators/` 子包，按类别分目录，每个可用指标独立文件，例如 `overlap/ema.py`、`overlap/sma.py`、`momentum/macd.py`。同一指标的 native/Pandas 等实现留在同一文件；文件负责明确的库调用和语义映射，不设 `backends/` 目录。

`types` 承载定义、结果和游标，`common` 负责共享输出验证，`calculus` 负责有限历史数学，`registry` 显式绑定 ID、backend、函数和实现版本，`runtime` 提供目录、纯计算与缓存。指标模块不导入注册表、运行时、策略或 Worker；只在缓存未命中的批量计算时调用，不增加逐 bar 包装。

目录拥有公共默认值、参数域、输出及别名；私有 Wrapper 接收必填的已规范化参数。多输出按已审核的供应商列名映射成规范通道，正确列交换顺序可归一，缺列、重复列或未知列报 `output-contract`，索引错位报 `index-mismatch`。适配层的 `IndicatorError` 原样通过，真实第三方异常包装为 `calculation-failed`。不 reindex 或填零掩盖违例。

旧 `indicator_api`、`indicator_methods`、`indicator_types` 是同对象兼容导出，保留旧导入和历史 pickle 读取；新实现与类型位于子包。`indicators.compute/catalog/describe` 和 `self.ta` 的调用方式不变。

## 时间、就绪与结果

策略直接行情入口 `self.open/high/low/close/volume/hl2/hlc3/hlcc4` 已复用 `IndicatorHandle` 与同运行游标，支持 `self.ta.ema(self.close)`。来源句柄的 metadata 标记为 `data-source`，不登记为指标、不影响逐根回调；其 valid 仍会影响实际消费它的指标。保存引用与切片动态更新，算术和显式转换仍是当时快照。

首次访问新序列捕获独立 OHLCV 快照，init 的后续读取、自定义或内置指标登记前及结束边界检测行情变化并报 `data-source-mutated`，行情加工应前移；额外列不影响该检查。新来源使用 float64 和有限性掩码，派生公式固定且每运行最多计算一次。逐 bar 不扫描全表；运行中经旧 DataFrame 修改行情与新来源混用不受支持，不保证实时检测。纯旧入口保留原行为。具体规则见实施设计与[内核使用说明](../../../README.md)。

`self.data_index/df/pip` 是原数据入口的委托，不能与句柄的 `.s/.df` 隔离转换混淆：保存的普通 pandas 对象不随游标更新，也不承诺深拷贝；pip 仍为估计。上述 11 个名字及 `bar_index/bar_state` 为保留字段，迁移同名策略参数时应改 Python 字段名，展示 title 不受影响。

每个 run 持有独立游标，登记指标及其普通容器别名、具名通道和时间切片都按同一游标读取前缀；每 bar 不调用后端；指标的必要输出掩码只用于就绪诊断，执行循环不扫描指标就绪状态。初始化可访问全量历史，因此框架不能阻止用户在 `init()` 中主动保存未来信息或写非因果 callable。

`ready` 表示最低历史条件满足，`valid` 表示通道在当前 bar 有可消费值。`ready_at/first_ready` 结合最低历史与必要输出的有效性，供诊断使用；`required_outputs=[]` 时只检查最低历史条件。它们均不控制策略执行；使用者自行处理无效数据。NaN/Inf 不构成有效数值。默认要求当前输入有效；valuewhen 保留已确认历史事件值，pivot_points 保留上一完整周期水平，按输出自身判断有效性。其余缺失恢复逐项声明，不自动填零或后向填充。

`next()` 从位置 0 开始，对每根正常到达的 bar 调用一次，包括历史不足、全 NaN 和中途缺口。首根只可见一条历史；读取上一根前检查长度，消费指标前检查对应通道 `valid`，尤其不要用 `bool(NaN)` 判断信号。既有订单和止损继续按 broker 的因果阶段处理；破产或异常会终止回调。运行正常结束、资金耗尽或抛出异常后，诊断句柄恢复完整历史并禁止再次登记。

`.s`、`.df`、`np.asarray()` 是当前可见前缀的显式快照，写入副本不会污染计算结果。原始缓冲区以不可写 bytes 为底层，不能通过 `setflags` 恢复写权限。缓存模板和不同 run 不共享游标；pickle 后恢复同样的只读约束。

结果 `attrs["indicator_snapshot"]` 保存 ID、语义版本、规范化参数、输入内容身份和组合来源、后端、`implementation_version` 与依赖版本、core 版本、dtype、单位描述和缺失/就绪策略；与既有 `input_snapshot` 并存。自定义 `ind()` 标记为 custom 且不共享缓存，不承诺任意 callable 的可复现性。

## 能力与特殊入口

| 分类        | 普通指标 | 工具/确认事件 | 形态 |
| ----------- | -------: | ------------: | ---: |
| candles     |        2 |             0 |    9 |
| cycles      |        8 |             0 |    0 |
| momentum    |       62 |             0 |    0 |
| overlap     |       49 |             0 |    0 |
| performance |        3 |             0 |    0 |
| statistics  |       13 |             0 |    0 |
| trend       |       29 |             2 |    0 |
| utility     |        0 |            22 |    0 |
| volatility  |       20 |             0 |    0 |
| volume      |       22 |             0 |    0 |

DPO 固定非居中、无前视模式。Ichimoku 固定关闭 Chikou 与未来扩展，只返回同索引的 `span_a/span_b/tenkan/kijun`。CPR 只按上一根输入 bar 计算，不提供跨周期重采样或 virgin 未来识别。VWAP 按输入日期索引的日/周/月分组，不推断交易所会话。

九种形态为 doji、inside、engulfing、hammer、shootingstar、harami、morningstar、eveningstar、marubozu，对应 cdl_ 方法。整数 0 表示有效但未触发；历史不足和缺失通过独立 valid 表达。doji 的正值只表示十字，inside 的符号表示当根方向，都不是独立多空建议；engulfing/harami 保留 80/100 强度。八项调用固定 classic 原生函数；doji 本地计算实体与前窗口波幅阈值，避免隐式 TA-Lib 和全样本 epsilon。未审核 cdl_pattern 分派仍不可用。

## 自定义指标与复用

自定义计算使用 `self.ind(func, *args, name=None, **kwargs)`，只在 `init()` 登记；旧 `self.I` 已删除，不提供别名。内置公式统一使用 `self.ta`。

同一个纯函数可按多组参数登记，也可放在普通可导入模块中由其他策略复用。每次登记都执行函数并返回独立句柄，不启用自定义缓存。DataFrame 的列顺序决定通道顺序，须通过 `name` 列表指定通道名；返回结果用 `result['middle']` 选择通道，再用于 `self.ta` 组合或绘图。

组合已有指标时，使用接收 `ta` 和来源的组合函数，并用 `NamedTuple` 等容器保存句柄即可；容器没有计算生命周期。不要把某个运行的句柄保存在全局对象供下一次运行复用。完整示例以 `@backtest` 声明策略，默认不下单；另一策略复用同一函数的路径也由示例测试实际执行。

[完整源码](../../../examples/strategies/custom_indicators.py)

`init()` 看得到完整输入历史，因此滚动公式必须只依赖当前及过去数据；改用句柄不能纠正负向 shift 等已发生的未来泄漏。`.s` 在示例中是供纯计算使用的完整输入快照，保存到策略属性的是登记后的句柄。算术结果同样是普通数组，需要动态读取时应通过 `ind` 重新登记。

自定义结果的 `valid` 默认取有限性，`ready` 默认全真；布尔 False 和整数 0 是有效值，并不表示历史不足。`warmup` 参数及元数据已移除；`ind(..., warmup=...)` 明确抛 `TypeError`，不会转发给 callable。所有通道都由消费者自行检查有效性。消费带掩码的单通道时可传入 `source.s.where(source.valid)`；`ind` 不自动传播参数中句柄的掩码，也不校验其中的运行归属。`required_outputs`、显式输出掩码、版本身份和缓存不是本入口的登记选项。

## `ind()` 结果消费约束

| 消费方式                                                   | 当前行为与迁移约束                                                                              |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `ind(callable, *args, **kwargs)`                           | 调用形式、名称和位置数组规则保持；返回 `IndicatorHandle`                                        |
| `len/shape/ndim/dtype`、索引、比较、基本算术、`float/bool` | 读取当前前缀；标量转换读取最新值                                                                |
| 属性、别名、嵌套 list/dict/tuple、通道解包、切片           | 保留游标引用，不再逐 bar 重绑属性                                                               |
| Series/DataFrame 返回值                                    | 索引必须与行情完全相同；旧的 RangeIndex 结果改为保留输入索引，或显式 `.to_numpy()` 声明位置数组 |
| `.s/.df/np.asarray`                                        | 显式快照，不能作为会自动增长的引用                                                              |
| 算术派生结果                                               | 普通数组；需要受控逐 bar 读取时显式再次 `ind()` 登记，不解析自动表达式图                        |
| 原地赋值、ufunc `out`、`np.asarray(copy=False)`            | 明确拒绝；先 `.copy()` 再修改                                                                   |
| ndarray 类型身份、任意方法表                               | 不承诺兼容；迁移到公开消费方法                                                                  |
| `resample_apply`、SignalStrategy、原生分数交易             | 使用统一句柄且保持价格单位；交易语义见[交易指南](trading.md)                                    |
| 历史 `_Indicator` pickle                                   | 保留旧类用于加载历史样本；新策略统一返回句柄                                                    |

示例见[内置指标用户脚本](../../../examples/strategies/ema_macd.py)，用户以 `@backtest` 声明策略，框架通过 `runtime` 接管。本次未接入桌面或 Worker。

## 性能与资源范围

`Backtest(..., indicator_cache_bytes=64 * 1024 * 1024)` 配置每个缓存实例的 LRU 保留字节预算，设为 `0` 完全关闭复用。计量覆盖数组、掩码和索引；活跃策略引用、临时数组、Python 对象及行情不属于预算，因此它不是进程 RSS 上限。超预算结果照常计算但不保留，淘汰不损坏活跃句柄，失败不缓存。

缓存开启且条目仍被保留时，单次 run 内复用相同登记。grid 优化在线程间共享缓存并合并同键并发计算，spawn 各 worker 独立缓存；只序列化调用 token，不序列化锁。SAMBO 的连续运行共享本次搜索缓存。池由本次优化创建和关闭；父进程 finally 释放本次缓存，worker 缓存随池退出释放。跨进程不承诺全局命中，最终最优 run 可以重新计算。

grid 原始行情只分配一次共享内存，批次复用描述符；父进程拥有释放责任。策略行情仍为私有可写副本，避免用户修改污染其他候选。共享列通过显式 `copy=False` 重建并验证内存共享；索引独立复制，运行私有行情仍会物化，不声称整个回测零拷贝。

对可写 DataFrame 每次登记重新读取、哈希所需输入；这是防止错误命中的必要开销。已登记结果不会追溯重算。当前不提供显式冻结行情 API、持久化缓存或跨进程结果共享。真实耗时、缓存收益及退化见实施记录，不把计数优化等同于所有工作负载提速。

性能验收以 10 万 bar 为上限，重点覆盖单策略 10、30、50 个不同指标及重复登记，分别计量初始化、后端、逐 bar 消费与总耗时；详细数据见实施记录。

## 新增或替换指标

1. 在对应类别新建指标文件，以无状态函数明确调用已审核算法并完成通道映射；未来形态同样每项独立文件。
2. 在 `indicators/catalog.json` 声明参数、输出及别名、固定选项、状态和有效性契约；默认值不在 Wrapper 另写一份。
3. 在 `indicators/registry.py` 显式登记函数及实现版本；同指标的不同实现仍放在该指标文件。版本进入 metadata 和缓存身份，修改映射须更新版本。
4. 运行 `uv run --locked python scripts/generate_indicator_api.py`，补独立上游参考值、参数边界、缺口、短历史、前缀因果和异常测试。完整性测试验证目录、244 个当前可用 ID、独立文件和绑定对应；新增指标时同步审核集合。
5. 更新来源清单、类别能力计数和文档，运行 `uv run --locked python scripts/check_package.py`、相关 pytest、构建及隔离 wheel 验证；性能仍以最多 10 万 bar 的多指标策略对照。

例如 EMA 在 `overlap/ema.py` 调用固定算法并命名单通道；MACD 在 `momentum/macd.py` 将供应商列名映射为 `macd/histogram/signal`；SMA 在 `overlap/sma.py` 同时维护 native 和 Pandas 实现。策略作者继续使用本页开头的 `self.ta` 示例。

## 新增能力与迁移

本轮新增 53 个可用入口：20 个普通/组合指标、22 个序列工具、2 个确认 Pivot 和 9 种形态。其中 doji/inside 原已列为延期，因此目录 ID 净增 51；不将通道数、别名或 TradingView 文章数计为指标数。

- 普通指标：smi_stochastic、crsi、pmo、rmi、alligator、gator、atr_stop、volatility_stop、ma_envelopes、starc、ac、ibs、frama、wavetrend、adr、rvol、rci、iii、wvad、pivot_points。
- 工具：highest/lowest、highestbars/lowestbars、rolling_sum/rolling_count、cum、running_max/running_min、change/shift/range、percentrank、percentile_nearest_rank/percentile_linear_interpolation、cross/crossover/crossunder、barssince/valuewhen、rising/falling。
- pivothigh/pivotlow 在右窗完成时输出 value/pivot_bar/confirmed_at，不在原极值位置回填；并列极值取最右。所有时间索引为输入的零起点 bar 位置。

```python
def init(self):
    self.fast = self.ta.ema(length=10)
    self.slow = self.ta.ema(length=30)
    self.cross = self.ta.crossover(self.fast, self.slow)
    self.event_price = self.ta.valuewhen(self.cross, "Close")
    self.pivot = self.ta.pivothigh(left=3, right=3)
    self.pattern = self.ta.cdl_engulfing()
    self.levels = self.ta.pivot_points(inputs={"anchor": "PeriodStart"})

def next(self):
    if self.pivot.value.valid[-1]:
        confirmed_price = self.pivot.value[-1]
    if self.pattern.valid[-1]:
        score = self.pattern[-1]
```

完整可运行策略见[扩展示例](../../../examples/strategies/confirmed_events.py)。PeriodStart 必须由调用者显式给出 0/1 序列；第一段无锚点历史不算完整周期。传统、Fibonacci、Woodie、Classic、DeMark、Camarilla 六种公式只消费上一完整周期，Woodie 另消费新周期 Open；当前周期新高不改已确认水平。它不推断交易所会话，不等于任意 TradingView 日线数据设置。

默认参数、种子、缺失规则、阈值和来源见[冻结契约](../../../tests/fixtures/indicator_expansion/contracts.json)；研究候选完整归属见[处置清单](../../../tests/fixtures/engine-indicator-coverage-disposition.json)。工具使用固定窗口及明确缺失规则，不承诺 Pine 的动态 length、隐式 na 跳过、重绘或逐 tick 行为。Alligator 不施加绘图位移；Volatility Stop 从首次反转的下一根开始输出，不回溯清空前缀。排序类按窗口计算，未构建全样本平方矩阵。

五个既有入口提升语义/实现版本到 2：NVI/PVI 按指数乘价格比率更新（length 为价格间隔，量比较相邻 bar），不再累计百分数收益；缺失/零前价输出无效但保持内部状态。Squeeze/Squeeze Pro 的 use_tr 实际切换真实波幅与 high-low；MSW 拒绝 period=1。重跑旧策略可能改变结果，旧 pickle 只读已存数值，不自动重算。旧 smi 仍是 Ergodic，新增随机动量使用 smi_stochastic。

## 本地锚点、有限观测与显式参数

`ta.anchored_vwap` 和 `ta.anchored_vwap_bands` 的 inputs 为 `source`、`volume`、`anchor`。策略中绑定同图表列名或句柄；不接受 pandas Series。锚点必须完整且严格为 0/1，先重置再累计当前行，首次锚点前无效。源或量非有限时该行无效并跳过；即使该行缺失也执行重置。有限负量报错，零量在已有正累计量时沿用结果，否则无效。带宽为成交量加权总体标准差乘 `stdev_mult`，首个正量观测宽度为零，三通道固定为 `vwap/lower/upper`；溢出报计算错误。

`ta.mode` 按最近 `length` 个有限观测计窗，不按连续 bar 计窗；并列频数选数值最小者，全部唯一也选最小。缺失值不消耗窗口，满窗后的缺失行仍有效。内部窗口、频数和候选堆有界，输出历史仍随输入长度增长。

五个扩展参数均保留原默认数值和 valid：`true_range(handle_na=True)` 缺失前收盘时使用 H-L，当前 Close 可以缺失，但 H/L 必须有限且有序；首根零振幅仍为零。`kc(use_true_range=False)` 使用平滑 H-L 波幅。`alma(floor=True)` 向下取整权重中心，保留固定后端的权重方向。`linreg(offset=...)` 在当前窗口拟合线的 `length-1-offset` 位置取值，不移动序列；负 offset 只外推当前拟合，`length=1` 继续无效。`pivot_points(developing=True)` 使用当前锚定区间，首锚点当根有效；无效 OHLC 会使该区间持续无效直至重置，Woodie 不支持此模式。

这些 API 是本地契约，不构成 TradingView 逐点等价证明；条件锚点不推断交易所会话。完整八项调用和逐通道防护见[本地指标示例](../../../examples/strategies/local_builtin_indicators.py)。
