# ta.tos_stdevall

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

**全区间标准差参考**。依赖全区间统计的研究入口，不作为逐根因果指标开放。

类别：统计；状态：仅供研究。

尚不可调用：对整个选定样本进行 polyfit 和标准差计算，历史输出依赖后续样本；须替换为因果定义才能开放。

## 输入、输出与参数

输入：`close`。输出规范名：`tos_stdevall`。

输出别名：无。

| 参数 | 类型 | 默认值 | 约束 |
| --- | --- | --- | --- |
| 无 | — | — | — |

## 语义与计算来源

语义版本：`1`。

参数与输出以本页目录字段为准；[共同指标契约](../../guides/indicators.md)说明调用阶段、缺失、有效性、确认时点与缓存边界。算法不承诺 Pine 等价。

| 字段 | 审核值 |
| --- | --- |
| `source` | `tos_stdevall` |
| `dtype` | `float64` |
| `unit` | `native` |
| `missing_policy` | `native-v1` |
| `causal` | `False` |
| `minimum` | `1` |
| `windows` | `[]` |
| `required` | `None` |
| `fixed` | `{}` |

`required=None` 使用默认必要输出；`required=[]` 不要求输出通道就绪。minimum/windows/history_sum/history_offset 共同确定最低历史长度；这些元数据不控制回调，实际消费还须检查 valid。未出现的字段使用定义默认值，详见 [IndicatorSpec](../indicator-api.md)。

验证定位：`tests/test_indicator_catalog.py`；完整使用例见[示例入口](../../examples.md)。

[返回分类目录](index.md)
