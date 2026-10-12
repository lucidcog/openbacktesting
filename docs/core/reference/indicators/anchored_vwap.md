# ta.anchored_vwap

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

**条件锚点 VWAP**。显式 0/1 锚点先重置再纳入当前观测；首锚点前无效，缺失源或量跳过，零量沿用已有正权重均值，负量拒绝。

类别：均线与价格；状态：可用。

## 使用方法

在 `init()` 登记，在 `next()` 检查所选通道的 `valid` 后读取当前值。

```python
def init(self):
    self.value = self.ta.anchored_vwap(inputs={'source': 'source', 'volume': 'Volume', 'anchor': 'anchor'})
    self.latest_value = None

def next(self):
    channel = self.value
    if channel.valid[-1]:
        self.latest_value = float(channel[-1])
```

用法选择通道 `vwap`；全部通道见下方输出表。

完整可执行来源：[逐项体验指标](../../../../examples/advanced/indicator_reference.py)，入口 `main`。在仓库根目录运行：

```sh
uv run --locked python examples/advanced/indicator_reference.py --indicator ta.anchored_vwap
```

示例输入：source 使用收盘价；anchor 每 20 根标记一次，须替换为真实周期起点。

`ready` 表示必要输出与最低历史条件是否就绪，`valid` 表示当前通道可消费；两者均不控制策略回调，next 从首根执行。示例逐通道检查 valid，NaN 不应参与交易判断。

### 调用签名

```python
self.ta.anchored_vwap(*, inputs: 'Inputs | None' = None, backend: 'str | None' = None, required_outputs: 'Sequence[str] | None' = None) -> 'IndicatorHandle'
```

## 输入、输出与参数

输入：`source, volume, anchor`。输出规范名：`vwap`。

输出别名：无。

| 参数 | 类型 | 默认值 | 约束 |
| --- | --- | --- | --- |
| 无 | — | — | — |

## 语义与计算来源

语义版本：`1`。

参数与输出以本页目录字段为准；[共同指标契约](../../guides/indicators.md)说明调用阶段、缺失、有效性、确认时点与缓存边界。算法不承诺 Pine 等价。

| 字段 | 审核值 |
| --- | --- |
| `source` | `anchored_vwap` |
| `kind` | `indicator` |
| `dtype` | `float64` |
| `unit` | `native` |
| `missing_policy` | `finite-observations-v1` |
| `validity` | `output` |
| `causal` | `True` |
| `minimum` | `1` |
| `windows` | `[]` |
| `required` | `None` |
| `fixed` | `{}` |

`required=None` 使用默认必要输出；`required=[]` 不要求输出通道就绪。minimum/windows/history_sum/history_offset 共同确定最低历史长度；这些元数据不控制回调，实际消费还须检查 valid。未出现的字段使用定义默认值，详见 [IndicatorSpec](../indicator-api.md)。

后端 `openbacktesting.numpy`；实现版本 `1`；源码 `src/openbacktesting/indicators/overlap/anchored_vwap.py`。

默认后端：`openbacktesting.numpy`。

验证定位：`tests/test_local_builtin_indicators.py`；完整使用例见[示例入口](../../examples.md)。

[返回分类目录](index.md)
