# 行情与稳定句柄

完整代码见[行情来源示例](../../../examples/strategies/data_sources.py)；以下方法片段放在 Strategy 子类中。

## 直接访问行情

`self.open/high/low/close/volume` 和 `self.hl2/hlc3/hlcc4` 返回只读 `IndicatorHandle`，保存引用和切片仍随本次运行游标更新，可在 `init()` 直接传给 `self.ta`：

```python
def init(self):
    self.saved_close = self.close
    self.tail = self.close[-3:]
    self.average = self.ta.ema(self.close, length=20)
    self.weighted_average = self.ta.ema(self.hlcc4, length=20)

def next(self):
    if self.average.valid[-1] and self.saved_close[-1] > self.average[-1]:
        pass
```

`hl2=(H+L)/2`、`hlc3=(H+L+C)/3`、`hlcc4=(H+L+C+C)/4`；后者不包含 Open。当前值用 `[-1]`，上一根用 `[-2]`，`[0]` 是首值，不采用 Pine 历史偏移。比较和算术产生普通数组，不自动跟随游标；条件判断应先取标量。`.s/.df/np.asarray()` 转换也是当时前缀的快照，init 主动保存的完整数据不会被撤回。

`self.data_index/df` 每次读取返回当前可见的普通 pandas 对象，保存后不随游标改变长度，不承诺深拷贝或内容隔离。df 保留原列名和额外列，不自动添加派生列。`self.pip` 沿用全样本小数位估计，不能用作可靠的交易所 tick size。

首次读取八个序列之一会捕获完整 OHLCV 和索引；同运行的新序列使用同一快照。**行情加工须在首次读取新序列前完成**：之后在 init 修改 OHLCV、dtype 或索引，会在后续新序列读取、指标登记或 init 结束时抛 `data-source-mutated`；仅增加额外列不受影响。新序列与运行中行情写入混用不受支持：旧 `self.data/df` 仍可写，但新句柄不跟随写入，也不保证立即检测。仅使用旧接口不启用新快照约束。

新来源统一为 float64，接受整数、浮点及 pandas 可空整数/浮点；拒绝布尔、复数、object 等类型，索引须唯一。缺失成交量保持 NaN；非有限输入和派生溢出通过 valid 标记无效，不填零。来源读取不增加指标数量；来源与指标的有效性均不影响逐根调用 `next()`。

上述 11 个属性名均为保留名，同名策略字段、方法、InputSpec 绑定字段和运行参数须改名，例如将参数 `close` 改为 `close_threshold`。InputSpec 的展示 `title="close"` 仍可用。旧 `self.data` 入口保留。

## 当前 bar 的位置与状态

`self.bar_index` 是当前输入 bar 的零起点整数位置；`self.data_index` 是可见历史的 pandas 标签索引，`self.data.index` 保留。顶层 `self.index` 已移除，不再保留该名字。

`self.bar_state` 返回冻结的 `BarState` 值，`is_first` 表示位置 0，`is_last` 表示固定输入的最后一根。单根输入两者同时为真；提前终止不把最后实际访问的 bar 改成 `is_last`。保存的状态是当时快照，不随游标更新。类型可从 `openbacktesting` 或 `openbacktesting.strategy` 导入。

状态在 `on_start()`（首根）、`next()`、订单/成交通知（含期末通知）可读；`init()`、`on_finish()` 和运行结束后的访问抛 `RuntimeError`。每次运行独立维护常量大小的当前上下文。

`bar_index/bar_state/data_index` 是只读保留属性，不允许同名类字段、方法、Input 绑定、运行参数、实例赋值或删除；Input 的展示标题仍可使用这些名字。

完整示例见 [bar_states.py](../../../examples/strategies/bar_states.py)。从首根调用 `next()`，此时只有一条可见历史：读取 `[-2]` 前检查长度，消费指标前检查对应通道的 `valid[-1]`。
