"""内部运行采集政策；默认行为与普通回测保持一致。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CollectionPolicy:
    portfolio: bool = True
    logs: bool = True
    plotting: bool = True


DEFAULT_COLLECTION = CollectionPolicy()
