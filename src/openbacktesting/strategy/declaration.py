"""作者回测声明：保持类身份，无全局注册和执行副作用。"""

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
    """将默认回测设置附在具体策略类上；实际行情和运行由宿主提供。

    只接受基础值和对应枚举成员；固定选项不接受裸字符串或其他枚举。
    仅支持带括号的装饰器形式。算法参数继续使用 inputs，不接受品种、
    周期或资源选项；配置模型由框架构造，返回原策略类。

    Args:
        cash: 正有限初始账户余额。
        spread: 每次买卖执行的价差小数比例，范围 [0,1)。
        commission_type: 单一佣金类型；PERCENT、CASH_PER_ORDER 或 CASH_PER_CONTRACT。
        commission_value: PERCENT 使用 [-10,10) 百分数，0.2 表示 0.2%，负值为返佣；
            其他类型为非负金额，分别按实际 Fill 或实际资产单位收取。
        risk_free_rate: (-1,1) 年化小数，仅用于统计，不向账户计息。
        default_qty_type: FIXED 为固定数量，PERCENT_OF_EQUITY 为权益百分数。
        default_qty_value: None 禁用默认数量；FIXED 为正数，权益百分数为 (0,100]。
            仅普通 buy/sell 省略 qty 时按请求时 Close 和权益预算、向零取整并冻结。
        margin: (0,1] 保证金小数比例，不放大默认数量预算。
        execution_timing: NEXT_OPEN 或 SAME_CLOSE；后者仅处理 next 新增无条件市价单。
        slippage_type: FIXED 为固定价格距离，BPS 为基点。
        slippage_value: 非负滑点值，零为无滑点。
        allow_short: 是否允许新增空头，严格 bool。
        max_gross_exposure: None 或正的总名义／权益倍数上限。
        hedging: 是否保留双向批次，严格 bool。
        exclusive_orders: 新普通入场是否撤旧入场并提交旧仓退出，严格 bool。
        end_policy: MARK_TO_MARKET 保留持仓估值，CLOSE_AT_LAST_CLOSE 清算实际持仓。

    Raises:
        TypeError: 类型、枚举、字段或装饰目标不合法。
        ValueError: 数值越界或同一策略重复声明。
    """
    settings = BacktestSettings(**locals())

    def decorate(cls: type[_S]) -> type[_S]:
        if not isinstance(cls, type) or not issubclass(cls, Strategy) or isabstract(cls):
            raise TypeError("backtest 只能装饰具体 Strategy 子类")
        if _ATTRIBUTE in vars(cls):
            raise ValueError("同一策略类不能重复应用 backtest")
        setattr(cls, _ATTRIBUTE, settings)
        return cls

    return decorate


def declaration(cls: type[Strategy]) -> BacktestSettings | None:
    """只读取本类的直接声明；未装饰子类不继承入口身份。"""
    value = vars(cls).get(_ATTRIBUTE)
    if value is None:
        return None
    if not isinstance(value, BacktestSettings):
        raise TypeError("策略回测声明无效")
    return value.resolve(None)
