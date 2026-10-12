"""可重建的线性费用值；不持有账户或策略状态。"""

from collections.abc import Mapping
from dataclasses import dataclass

from openbacktesting.broker.models import finite


@dataclass(frozen=True)
class Commission:
    """每次成交固定额、金额比例和每资产单位费用；比例 0.002 表示 0.2%。"""

    fixed: float = 0.0
    relative: float = 0.0
    per_unit: float = 0.0

    def __post_init__(self):
        for name in ("fixed", "relative", "per_unit"):
            object.__setattr__(self, name, finite(getattr(self, name), f"commission_{name}"))
        if self.fixed < 0 or self.per_unit < 0 or not -0.1 <= self.relative < 0.1:
            raise ValueError("手续费配置超出允许范围")

    def calculate(self, qty: float, price: float) -> float:
        """按实际成交数量与价格计算费用；调用方负责成交值校验。"""
        return self.fixed + abs(qty) * price * self.relative + abs(qty) * self.per_unit

    def snapshot(self) -> dict:
        """导出带模型版本的独立纯值。"""
        return {
            "kind": "linear",
            "version": 1,
            "fixed": self.fixed,
            "relative": self.relative,
            "per_unit": self.per_unit,
        }

    @classmethod
    def from_snapshot(cls, value: Mapping) -> "Commission":
        """严格恢复完整快照；拒绝未知版本、字段或隐式默认。"""
        if not isinstance(value, Mapping):
            raise TypeError("Commission 快照必须为映射")
        if set(value) != {"kind", "version", "fixed", "relative", "per_unit"}:
            raise ValueError("Commission 快照字段不完整或未知")
        if value["kind"] != "linear" or type(value["version"]) is not int or value["version"] != 1:
            raise ValueError("Commission 快照模型或版本不支持")
        return cls(value["fixed"], value["relative"], value["per_unit"])


def normalize_commission(value: float | tuple[float, float] | Commission) -> Commission:
    """将旧费用输入规范化为纯值模型；不接受 callable。"""
    if isinstance(value, Commission):
        return value
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError("commission 元组必须包含固定额和比例")
        return Commission(fixed=value[0], relative=value[1])
    return Commission(relative=value)
