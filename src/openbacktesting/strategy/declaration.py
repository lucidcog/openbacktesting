"""Author backtest declaration preserving class identity, without global registration or execution side effects."""

from collections.abc import Callable
from inspect import isabstract
from typing import TypeVar

from openbacktesting.simulation.config import (
    BacktestSettings,
    CommissionType,
    EndPolicy,
    ExecutionTiming,
    QuantityType,
    SlippageType,
)
from openbacktesting.strategy.base import Strategy

_S = TypeVar("_S", bound=Strategy)
_ATTRIBUTE = "_openbacktesting_backtest_settings"


def backtest(
    *,
    cash: float = 10_000,
    spread: float = 0.0,
    commission_type: CommissionType = CommissionType.PERCENT,
    commission_value: float = 0.0,
    risk_free_rate: float = 0.0,
    default_qty_type: QuantityType = QuantityType.FIXED,
    default_qty_value: float | None = None,
    margin: float = 1.0,
    execution_timing: ExecutionTiming = ExecutionTiming.NEXT_OPEN,
    slippage_type: SlippageType = SlippageType.BPS,
    slippage_value: float = 0.0,
    allow_short: bool = True,
    max_gross_exposure: float | None = None,
    hedging: bool = False,
    exclusive_orders: bool = False,
    end_policy: EndPolicy = EndPolicy.MARK_TO_MARKET,
) -> Callable[[type[_S]], type[_S]]:
    """Attach default backtest settings to a concrete strategy class; the host supplies actual market data and execution.

    Accept only primitive values and corresponding enum members; fixed options reject bare strings and other enums.
    Only the decorator form with parentheses is supported. Algorithm parameters still use inputs; instrument,
    timeframe, and resource options are not accepted. The framework constructs the configuration model and returns the original strategy class.

    Args:
        cash: Positive finite initial account balance.
        spread: Fractional spread for every buy/sell execution, in [0,1).
        commission_type: One commission type: PERCENT, CASH_PER_ORDER, or CASH_PER_CONTRACT.
        commission_value: PERCENT uses percentage points in [-10,10); 0.2 means 0.2%, and negative values are rebates;
            other types use nonnegative amounts, charged per actual Fill or actual asset unit respectively.
        risk_free_rate: Annualized fraction in (-1,1), used only for statistics without accruing account interest.
        default_qty_type: FIXED means fixed quantity; PERCENT_OF_EQUITY means equity percentage.
        default_qty_value: None disables default sizing; FIXED is positive, and equity percentage is in (0,100].
            Only ordinary buy/sell orders omitting qty use Close and equity at request time to budget, round toward zero, and freeze quantity.
        margin: Margin fraction in (0,1], without amplifying the default quantity budget.
        execution_timing: NEXT_OPEN or SAME_CLOSE; the latter handles only new unconditional market orders from next.
        slippage_type: FIXED means a fixed price distance; BPS means basis points.
        slippage_value: Nonnegative slippage value; zero means no slippage.
        allow_short: Whether new short positions are allowed; strictly bool.
        max_gross_exposure: None or a positive cap on gross notional/equity.
        hedging: Whether to retain two-sided lots; strictly bool.
        exclusive_orders: Whether a new ordinary entry cancels prior entries and submits exits for existing positions; strictly bool.
        end_policy: MARK_TO_MARKET retains marked positions; CLOSE_AT_LAST_CLOSE liquidates actual positions.

    Raises:
        TypeError: Invalid types, enums, fields, or decorator targets.
        ValueError: Out-of-range numbers or duplicate declarations on the same strategy.
    """
    settings = BacktestSettings(**locals())

    def decorate(cls: type[_S]) -> type[_S]:
        if not isinstance(cls, type) or not issubclass(cls, Strategy) or isabstract(cls):
            raise TypeError("backtest can decorate only concrete Strategy subclasses")
        if _ATTRIBUTE in vars(cls):
            raise ValueError("backtest cannot be applied repeatedly to the same strategy class")
        setattr(cls, _ATTRIBUTE, settings)
        return cls

    return decorate


def declaration(cls: type[Strategy]) -> BacktestSettings | None:
    """Read only this class's direct declaration; undecorated subclasses do not inherit entry-point identity."""
    value = vars(cls).get(_ATTRIBUTE)
    if value is None:
        return None
    if not isinstance(value, BacktestSettings):
        raise TypeError("Invalid strategy backtest declaration")
    return value.resolve(None)
