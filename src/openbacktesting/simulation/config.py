"""Exportable default backtest settings independent of strategies, hosts, and execution lifecycles."""

from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from enum import Enum

from openbacktesting.broker.commission import Commission
from openbacktesting.broker.execution import Slippage
from openbacktesting.broker.models import finite
from openbacktesting.portfolio.rates import validate_risk_free_rate


class CommissionType(Enum):
    """Author-facing commission type; PERCENT uses percentage points, and other members use account amounts."""

    PERCENT = "percent"
    CASH_PER_ORDER = "cash_per_order"
    CASH_PER_CONTRACT = "cash_per_contract"


class QuantityType(Enum):
    """Default order size: Fixed asset quantity or a percentage of equity at request time."""

    FIXED = "fixed"
    PERCENT_OF_EQUITY = "percent_of_equity"


class SlippageType(Enum):
    """Slippage distance: Fixed price units or basis points of price."""

    FIXED = "fixed"
    BPS = "bps"


class ExecutionTiming(Enum):
    """Execution timing: Process no earlier than the next bar, or process new unconditional market orders at this bar's close."""

    NEXT_OPEN = "next_open"
    SAME_CLOSE = "same_close"


class EndPolicy(Enum):
    """End policy: Retain marked positions or liquidate actual positions at the final close."""

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
    """Convert exact strings to corresponding enum members only at the host boundary."""
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
                raise ValueError(f"{name} must be one of: {choices}") from None
        elif not isinstance(value, kind):
            raise TypeError(f"{name} must be {kind.__name__} member or corresponding string")
    return result


@dataclass(frozen=True)
class DefaultOrderSize:
    """Request budget when ordinary orders omit qty; does not represent a target position or filled notional."""

    mode: str
    value: float

    def __post_init__(self):
        if self.mode not in ("fixed", "equity_fraction"):
            raise ValueError("mode must be fixed or equity_fraction")
        object.__setattr__(self, "value", finite(self.value, "value", positive=True))
        if self.mode == "equity_fraction" and self.value > 1:
            raise ValueError("equity_fraction must be in (0, 1]")

    def snapshot(self) -> dict:
        """Export independent mode and value."""
        return {"mode": self.mode, "value": self.value}

    @classmethod
    def from_snapshot(cls, value: Mapping) -> "DefaultOrderSize":
        """Strictly restore complete configuration without filling missing fields."""
        if not isinstance(value, Mapping):
            raise TypeError("DefaultOrderSize snapshot must be a mapping")
        if set(value) != {"mode", "value"}:
            raise ValueError("DefaultOrderSize snapshot has missing or unknown fields")
        return cls(value["mode"], value["value"])


def validate_order_size(value: DefaultOrderSize | None) -> DefaultOrderSize | None:
    """Accept only validated immutable models or explicit clearing."""
    if value is not None and not isinstance(value, DefaultOrderSize):
        raise TypeError("default_order_size must be DefaultOrderSize or None")
    return value


@dataclass(frozen=True)
class BacktestSettings:
    """Flat immutable author-facing settings; validate enums and numbers after decoding at the host boundary."""

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
                raise TypeError(f"{name} must be {kind.__name__} member")
        object.__setattr__(self, "risk_free_rate", validate_risk_free_rate(self.risk_free_rate))
        for name in ("cash", "margin"):
            object.__setattr__(self, name, finite(getattr(self, name), name, positive=True))
        spread = finite(self.spread, "spread")
        object.__setattr__(self, "spread", spread)
        if self.margin > 1:
            raise ValueError("margin must be in (0,1]")
        if not 0 <= spread < 1:
            raise ValueError("spread must be in [0,1)")
        if self.max_gross_exposure is not None:
            object.__setattr__(
                self,
                "max_gross_exposure",
                finite(self.max_gross_exposure, "max_gross_exposure", positive=True),
            )
        for name in ("allow_short", "hedging", "exclusive_orders"):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        value = finite(self.commission_value, "commission_value")
        if self.commission_type is CommissionType.PERCENT:
            if not -10 <= value < 10:
                raise ValueError("commission_value percentage must be in [-10,10)")
        elif value < 0:
            raise ValueError("commission_value amount must not be negative")
        object.__setattr__(self, "commission_value", value)
        if self.default_qty_value is not None:
            value = finite(self.default_qty_value, "default_qty_value", positive=True)
            if self.default_qty_type is QuantityType.PERCENT_OF_EQUITY and value > 100:
                raise ValueError("default_qty_value equity percentage must be in (0,100]")
            object.__setattr__(self, "default_qty_value", value)
        value = finite(self.slippage_value, "slippage_value")
        if value < 0:
            raise ValueError("slippage_value must not be negative")
        object.__setattr__(self, "slippage_value", value)

    def _values(self) -> dict:
        return {field.name: getattr(self, field.name) for field in fields(self)}

    def kwargs(self) -> dict:
        """Adapt to low-level Backtest arguments, separately from flat snapshots and the override allowlist."""
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
        """Decode sparse host overrides; a changed type must be supplied together with a new value."""
        if overrides is None:
            overrides = {}
        if not isinstance(overrides, Mapping):
            raise TypeError("settings must be a mapping or None")
        unknown = set(overrides).difference(self._values())
        if unknown:
            raise ValueError(f"Unknown backtest setting: {list(unknown)!r}")
        values = _decode_enums(overrides)
        for type_name, value_name in _PAIRED_FIELDS:
            if (
                type_name in values
                and values[type_name] is not getattr(self, type_name)
                and value_name not in values
            ):
                raise ValueError(f"Changing {type_name} requires also supplying {value_name}")
        return replace(self, **values)

    def snapshot(self) -> dict:
        """Export all flat fields; enums become strings and percentages retain author units."""
        return {
            name: value.value if isinstance(value, Enum) else value
            for name, value in self._values().items()
        }

    @classmethod
    def from_snapshot(cls, value: Mapping) -> "BacktestSettings":
        """Strictly restore complete JSON settings; sparse fields and Python enums are not accepted."""
        if not isinstance(value, Mapping):
            raise TypeError("Backtest settings snapshot must be a mapping")
        if set(value) != {field.name for field in fields(cls)}:
            raise ValueError("Backtest settings snapshot has missing or unknown fields")
        for name, item in value.items():
            if type(item) not in (str, int, float, bool, type(None)):
                raise TypeError(f"{name} must be a JSON primitive")
        return cls(**_decode_enums(value))
