"""可导出回测默认设置；不依赖策略、宿主或执行生命周期。"""

from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from enum import Enum

from openbacktesting.broker.commission import Commission
from openbacktesting.broker.execution import Slippage
from openbacktesting.broker.models import finite
from openbacktesting.portfolio.rates import validate_risk_free_rate


class CommissionType(Enum):
    """作者佣金类型；PERCENT 使用百分数，其余成员使用账户金额。"""

    PERCENT = "percent"
    CASH_PER_ORDER = "cash_per_order"
    CASH_PER_CONTRACT = "cash_per_contract"


class QuantityType(Enum):
    """默认下单量：固定资产数量，或请求时权益的百分数。"""

    FIXED = "fixed"
    PERCENT_OF_EQUITY = "percent_of_equity"


class SlippageType(Enum):
    """滑点距离：固定价格单位，或价格的基点数。"""

    FIXED = "fixed"
    BPS = "bps"


class ExecutionTiming(Enum):
    """执行时机：最早下一根处理，或本根收盘处理新增无条件市价单。"""

    NEXT_OPEN = "next_open"
    SAME_CLOSE = "same_close"


class EndPolicy(Enum):
    """期末政策：保留持仓估值，或按末收盘价清算实际持仓。"""

    MARK_TO_MARKET = "mark_to_market"
    CLOSE_AT_LAST_CLOSE = "close_at_last_close"


_ENUM_FIELDS = {
    "commission_type": CommissionType,
    "default_qty_type": QuantityType,
    "slippage_type": SlippageType,
    "execution_timing": ExecutionTiming,
    "end_policy": EndPolicy,
}
_PAIRED_FIELDS = (
    ("commission_type", "commission_value"),
    ("default_qty_type", "default_qty_value"),
    ("slippage_type", "slippage_value"),
)


def _decode_enums(values: Mapping) -> dict:
    """只在宿主边界将精确字符串转换为对应枚举。"""
    result = dict(values)
    for name, kind in _ENUM_FIELDS.items():
        if name not in result:
            continue
        value = result[name]
        if type(value) is str:
            try:
                result[name] = kind(value)
            except ValueError:
                choices = ", ".join(member.value for member in kind)
                raise ValueError(f"{name} 必须为以下选项之一: {choices}") from None
        elif not isinstance(value, kind):
            raise TypeError(f"{name} 必须为 {kind.__name__} 成员或对应字符串")
    return result


@dataclass(frozen=True)
class DefaultOrderSize:
    """普通下单省略 qty 时的请求预算；不代表目标仓位或成交金额。"""

    mode: str
    value: float

    def __post_init__(self):
        if self.mode not in ("fixed", "equity_fraction"):
            raise ValueError("mode 必须为 fixed 或 equity_fraction")
        object.__setattr__(self, "value", finite(self.value, "value", positive=True))
        if self.mode == "equity_fraction" and self.value > 1:
            raise ValueError("equity_fraction 必须在 (0, 1]")

    def snapshot(self) -> dict:
        """导出独立的模式和值。"""
        return {"mode": self.mode, "value": self.value}

    @classmethod
    def from_snapshot(cls, value: Mapping) -> "DefaultOrderSize":
        """严格恢复完整配置，不填补缺失字段。"""
        if not isinstance(value, Mapping):
            raise TypeError("DefaultOrderSize 快照必须为映射")
        if set(value) != {"mode", "value"}:
            raise ValueError("DefaultOrderSize 快照字段不完整或未知")
        return cls(value["mode"], value["value"])


def validate_order_size(value: DefaultOrderSize | None) -> DefaultOrderSize | None:
    """只接受已验证的不可变模型或显式清空。"""
    if value is not None and not isinstance(value, DefaultOrderSize):
        raise TypeError("default_order_size 必须为 DefaultOrderSize 或 None")
    return value


@dataclass(frozen=True)
class BacktestSettings:
    """作者通道的平铺不可变设置；枚举与数值在宿主边界解码后校验。"""

    cash: float = 10_000
    spread: float = 0.0
    commission_type: CommissionType = CommissionType.PERCENT
    commission_value: float = 0.0
    risk_free_rate: float = 0.0
    default_qty_type: QuantityType = QuantityType.FIXED
    default_qty_value: float | None = None
    margin: float = 1.0
    execution_timing: ExecutionTiming = ExecutionTiming.NEXT_OPEN
    slippage_type: SlippageType = SlippageType.BPS
    slippage_value: float = 0.0
    allow_short: bool = True
    max_gross_exposure: float | None = None
    hedging: bool = False
    exclusive_orders: bool = False
    end_policy: EndPolicy = EndPolicy.MARK_TO_MARKET

    def __post_init__(self):
        for name, kind in _ENUM_FIELDS.items():
            if not isinstance(getattr(self, name), kind):
                raise TypeError(f"{name} 必须为 {kind.__name__} 成员")
        object.__setattr__(self, "risk_free_rate", validate_risk_free_rate(self.risk_free_rate))
        for name in ("cash", "margin"):
            object.__setattr__(self, name, finite(getattr(self, name), name, positive=True))
        spread = finite(self.spread, "spread")
        object.__setattr__(self, "spread", spread)
        if self.margin > 1:
            raise ValueError("margin 必须在 (0,1]")
        if not 0 <= spread < 1:
            raise ValueError("spread 必须在 [0,1)")
        if self.max_gross_exposure is not None:
            object.__setattr__(
                self,
                "max_gross_exposure",
                finite(self.max_gross_exposure, "max_gross_exposure", positive=True),
            )
        for name in ("allow_short", "hedging", "exclusive_orders"):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} 必须为 bool")
        value = finite(self.commission_value, "commission_value")
        if self.commission_type is CommissionType.PERCENT:
            if not -10 <= value < 10:
                raise ValueError("commission_value 百分数必须在 [-10,10)")
        elif value < 0:
            raise ValueError("commission_value 金额不得为负")
        object.__setattr__(self, "commission_value", value)
        if self.default_qty_value is not None:
            value = finite(self.default_qty_value, "default_qty_value", positive=True)
            if self.default_qty_type is QuantityType.PERCENT_OF_EQUITY and value > 100:
                raise ValueError("default_qty_value 权益百分数必须在 (0,100]")
            object.__setattr__(self, "default_qty_value", value)
        value = finite(self.slippage_value, "slippage_value")
        if value < 0:
            raise ValueError("slippage_value 不得为负")
        object.__setattr__(self, "slippage_value", value)

    def _values(self) -> dict:
        return {field.name: getattr(self, field.name) for field in fields(self)}

    def kwargs(self) -> dict:
        """适配为低层 Backtest 参数；与平铺快照及覆盖白名单分开。"""
        result = self._values()
        for type_name, value_name in _PAIRED_FIELDS:
            del result[type_name], result[value_name]
        if self.commission_type is CommissionType.PERCENT:
            commission = Commission(relative=self.commission_value / 100)
        elif self.commission_type is CommissionType.CASH_PER_ORDER:
            commission = Commission(fixed=self.commission_value)
        else:
            commission = Commission(per_unit=self.commission_value)
        size = None
        if self.default_qty_value is not None:
            size = (
                DefaultOrderSize("fixed", self.default_qty_value)
                if self.default_qty_type is QuantityType.FIXED
                else DefaultOrderSize("equity_fraction", self.default_qty_value / 100)
            )
        return result | {
            "commission": commission,
            "default_order_size": size,
            "slippage": Slippage(self.slippage_type.value, self.slippage_value),
            "execution_timing": self.execution_timing.value,
            "end_policy": self.end_policy.value,
        }

    def resolve(self, overrides: Mapping | None) -> "BacktestSettings":
        """解码宿主稀疏覆盖；不同类型必须与新数值一同提供。"""
        if overrides is None:
            overrides = {}
        if not isinstance(overrides, Mapping):
            raise TypeError("settings 必须为映射或 None")
        unknown = set(overrides).difference(self._values())
        if unknown:
            raise ValueError(f"未知回测设置: {list(unknown)!r}")
        values = _decode_enums(overrides)
        for type_name, value_name in _PAIRED_FIELDS:
            if (
                type_name in values
                and values[type_name] is not getattr(self, type_name)
                and value_name not in values
            ):
                raise ValueError(f"切换 {type_name} 必须同时提供 {value_name}")
        return replace(self, **values)

    def snapshot(self) -> dict:
        """导出全部平铺字段；枚举为字符串，百分数保留作者单位。"""
        return {
            name: value.value if isinstance(value, Enum) else value
            for name, value in self._values().items()
        }

    @classmethod
    def from_snapshot(cls, value: Mapping) -> "BacktestSettings":
        """从完整 JSON 设置严格恢复；不接受稀疏字段或 Python 枚举。"""
        if not isinstance(value, Mapping):
            raise TypeError("回测设置快照必须为映射")
        if set(value) != {field.name for field in fields(cls)}:
            raise ValueError("回测设置快照字段不完整或未知")
        for name, item in value.items():
            if type(item) not in (str, int, float, bool, type(None)):
                raise TypeError(f"{name} 必须为 JSON 基础值")
        return cls(**_decode_enums(value))
