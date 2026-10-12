"""固定历史输入的不可变 Bar 状态。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BarState:
    """当前执行位置的首尾快照；保存后不随运行游标变化。

    is_first 表示本次输入第 0 根；is_last 表示本次输入末根，不等同于运行结束。
    """

    is_first: bool
    is_last: bool
