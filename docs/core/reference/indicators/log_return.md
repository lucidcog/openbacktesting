# ta.log_return

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

**对数收益**。计算价格比率的对数，可选累计方式。

类别：收益与回撤；状态：可用。

## 使用方法

在 `init()` 登记，在 `next()` 检查所选通道的 `valid` 后读取当前值。

```python
def init(self):
    self.value = self.ta.log_return(self.close)
    self.latest_value = None

def next(self):
    channel = self.value
    if channel.valid[-1]:
        self.latest_value = float(channel[-1])
```

用法选择通道 `log_return`；全部通道见下方输出表。

完整可执行来源：[逐项体验指标](../../../../examples/advanced/indicator_reference.py)，入口 `main`。在仓库根目录运行：

```sh
uv run --locked python examples/advanced/indicator_reference.py --indicator ta.log_return
```

示例输入：随包 GOOG 的对应行情列。

`ready` 表示必要输出与最低历史条件是否就绪，`valid` 表示当前通道可消费；两者均不控制策略回调，next 从首根执行。示例逐通道检查 valid，NaN 不应参与交易判断。

### 调用签名

```python
self.ta.log_return(source: 'Source | None' = None, *, length: 'int' = 1, cumulative: 'bool' = False, inputs: 'Inputs | None' = None, backend: 'str | None' = None, required_outputs: 'Sequence[str] | None' = None) -> 'IndicatorHandle'
```

## 输入、输出与参数

输入：`close`。输出规范名：`log_return`。

输出别名：无。

| 参数 | 类型 | 默认值 | 约束 |
| --- | --- | --- | --- |
| `length` | `int` | `1` | 最小值：`1` |
| `cumulative` | `bool` | `False` | 无额外约束 |

## 语义与计算来源

语义版本：`1`。

参数与输出以本页目录字段为准；[共同指标契约](../../guides/indicators.md)说明调用阶段、缺失、有效性、确认时点与缓存边界。算法不承诺 Pine 等价。

| 字段 | 审核值 |
| --- | --- |
| `source` | `log_return` |
| `dtype` | `float64` |
| `unit` | `native` |
| `missing_policy` | `native-v1` |
| `causal` | `True` |
| `minimum` | `1` |
| `windows` | `['length']` |
| `required` | `None` |
| `fixed` | `{}` |

`required=None` 使用默认必要输出；`required=[]` 不要求输出通道就绪。minimum/windows/history_sum/history_offset 共同确定最低历史长度；这些元数据不控制回调，实际消费还须检查 valid。未出现的字段使用定义默认值，详见 [IndicatorSpec](../indicator-api.md)。

后端 `pandas-ta-classic.native`；实现版本 `1`；源码 `src/openbacktesting/indicators/performance/log_return.py`。

默认后端：`pandas-ta-classic.native`。

验证定位：`tests/test_indicator_catalog.py`；完整使用例见[示例入口](../../examples.md)。

[返回分类目录](index.md)
