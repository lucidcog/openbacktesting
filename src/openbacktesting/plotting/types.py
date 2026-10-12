"""绘图声明的不可变身份、预算与稳定错误；不包含渲染能力。"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any


class PlottingError(ValueError):
    """绘图契约错误，code 为可供调用者分派的稳定类别。"""

    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class PlottingLimits:
    """采集预算；所有上限均为正整数，bytes 在显式导出时检查。

    points 按唯一密集源计数，包含五列行情与两列执行掩码。
    panes 包含主图；plots 包含填充；events 包含每次颜色调用、标记和交易事实。
    text 为作者身份、标题、单位及标记文本的累计 UTF-8 字节数。
    """

    panes: int = 32
    plots: int = 256
    points: int = 10_000_000
    events: int = 1_000_000
    text: int = 1_048_576
    bytes: int = 268_435_456

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value <= 0:
                raise PlottingError("invalid-limit", f"{field.name} 必须为正整数")


@dataclass(frozen=True)
class _Ref:
    id: str
    title: str
    _owner: Any


@dataclass(frozen=True)
class PaneRef(_Ref):
    """当前运行的副图身份；仅将此引用传给 pane 参数。"""


@dataclass(frozen=True)
class PlotRef(_Ref):
    """线、柱或水平线的身份，可作为 fill 端点。"""


@dataclass(frozen=True)
class FillRef(_Ref):
    """两个兼容图层之间的填充身份。"""


@dataclass(frozen=True)
class MarkerRef(_Ref):
    """一次运行标记的身份。"""


class _Snapshot(tuple):
    """不可变纯值元组；整个 result.attrs 仍可 JSON 编码。"""

    __slots__ = ()

    def __new__(cls, version: str, payload: str, byte_limit: int):
        return super().__new__(cls, (version, payload, byte_limit, len(payload.encode())))

    def __getnewargs__(self):
        return self[:3]

    @property
    def version(self):
        return self[0]

    @property
    def payload(self):
        return self[1]

    @property
    def byte_limit(self):
        return self[2]

    @property
    def byte_length(self):
        return self[3]
