# ta.vp

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

**成交量分布**。按价格区间汇总成交量，输出不是逐根同索引序列，因此未开放。

类别：成交量；状态：非逐根序列。

尚不可调用：Volume Profile 输出按价格分箱，行数为 width，不属于行情时间序列。

## 输入、输出与参数

输入：`close, volume`。输出规范名：`vp`。

输出别名：无。

| 参数 | 类型 | 默认值 | 约束 |
| --- | --- | --- | --- |
| 无 | — | — | — |

## 语义与计算来源

语义版本：`1`。

参数与输出以本页目录字段为准；[共同指标契约](../../guides/indicators.md)说明调用阶段、缺失、有效性、确认时点与缓存边界。算法不承诺 Pine 等价。

| 字段 | 审核值 |
| --- | --- |
| `source` | `vp` |
| `dtype` | `float64` |
| `unit` | `native` |
| `missing_policy` | `native-v1` |
| `causal` | `True` |
| `minimum` | `1` |
| `windows` | `[]` |
| `required` | `None` |
| `fixed` | `{}` |

`required=None` 使用默认必要输出；`required=[]` 不要求输出通道就绪。minimum/windows/history_sum/history_offset 共同确定最低历史长度；这些元数据不控制回调，实际消费还须检查 valid。未出现的字段使用定义默认值，详见 [IndicatorSpec](../indicator-api.md)。

验证定位：`tests/test_indicator_catalog.py`；完整使用例见[示例入口](../../examples.md)。

[返回分类目录](index.md)
