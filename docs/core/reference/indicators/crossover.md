# ta.crossover

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

**上穿序列**。当前左值大于右值、前一根小于或等于时标记上穿；返回历史序列。

类别：序列工具；状态：可用。

## 使用方法

在 `init()` 登记，在 `next()` 检查所选通道的 `valid` 后读取当前值。

```python
def init(self):
    self.value = self.ta.crossover(inputs={'left': 'left', 'right': 'right'})
    self.latest_value = None

def next(self):
    channel = self.value
    if channel.valid[-1]:
        self.latest_value = float(channel[-1])
```

用法选择通道 `crossover`；全部通道见下方输出表。

完整可执行来源：[逐项体验指标](../../../../examples/advanced/indicator_reference.py)，入口 `main`。在仓库根目录运行：

```sh
uv run --locked python examples/advanced/indicator_reference.py --indicator ta.crossover
```

示例输入：left 为 3 根收盘均值；right 为 10 根收盘均值。

`ready` 表示必要输出与最低历史条件是否就绪，`valid` 表示当前通道可消费；两者均不控制策略回调，next 从首根执行。示例逐通道检查 valid，NaN 不应参与交易判断。

### 调用签名

```python
self.ta.crossover(left: 'Source | None' = None, right: 'Source | None' = None, *, inputs: 'Inputs | None' = None, backend: 'str | None' = None, required_outputs: 'Sequence[str] | None' = None) -> 'IndicatorHandle'
```

## 输入、输出与参数

输入：`left, right`。输出规范名：`crossover`。

输出别名：无。

| 参数 | 类型 | 默认值 | 约束 |
| --- | --- | --- | --- |
| 无 | — | — | — |

## 语义与计算来源

语义版本：`1`。

参数与输出以本页目录字段为准；[共同指标契约](../../guides/indicators.md)说明调用阶段、缺失、有效性、确认时点与缓存边界。算法不承诺 Pine 等价。

| 字段 | 审核值 |
| --- | --- |
| `source` | `crossover` |
| `kind` | `utility` |
| `dtype` | `float64` |
| `unit` | `native` |
| `missing_policy` | `finite-window-reset-v1` |
| `causal` | `True` |
| `minimum` | `2` |
| `windows` | `[]` |
| `history_sum` | `[]` |
| `history_offset` | `0` |
| `required` | `None` |
| `fixed` | `{}` |
| `input_args` | `['left', 'right']` |

`required=None` 使用默认必要输出；`required=[]` 不要求输出通道就绪。minimum/windows/history_sum/history_offset 共同确定最低历史长度；这些元数据不控制回调，实际消费还须检查 valid。未出现的字段使用定义默认值，详见 [IndicatorSpec](../indicator-api.md)。

后端 `openbacktesting.numpy`；实现版本 `1`；源码 `src/openbacktesting/indicators/utility/crossover.py`。

默认后端：`openbacktesting.numpy`。

验证定位：`tests/test_indicator_expansion.py`；完整使用例见[示例入口](../../examples.md)。

[返回分类目录](index.md)
