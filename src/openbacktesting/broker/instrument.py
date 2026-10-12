"""显式资产单位，不从行情小数位推断交易规则。"""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR, ROUND_HALF_UP, Decimal, localcontext

import numpy as np

from openbacktesting.broker.models import finite


@dataclass(frozen=True)
class InstrumentSpec:
    """真实资产数量与价格网格；currency仅作标签。"""

    symbol: str = "asset"
    quantity_step: float = 1
    min_quantity: float | None = None
    price_tick: float | None = None
    min_notional: float = 0
    currency: str | None = None

    def __post_init__(self):
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("symbol 必须为非空字符串")
        if self.currency is not None and not isinstance(self.currency, str):
            raise TypeError("currency 必须为字符串或None")
        step = finite(self.quantity_step, "quantity_step", positive=True)
        minimum = (
            step
            if self.min_quantity is None
            else finite(self.min_quantity, "min_quantity", positive=True)
        )
        object.__setattr__(self, "quantity_step", step)
        object.__setattr__(self, "min_quantity", minimum)
        if self.price_tick is not None:
            object.__setattr__(
                self, "price_tick", finite(self.price_tick, "price_tick", positive=True)
            )
        object.__setattr__(self, "min_notional", finite(self.min_notional, "min_notional"))
        if self.min_notional < 0:
            raise ValueError("min_notional 不得为负")

    def quantity(self, value, *, floor=False, opening=True) -> float:
        """直接请求必须在网格；预算数量可向零取整。"""
        value = finite(value, "qty")
        if value < 0:
            raise ValueError("qty 不得为负")
        lots = Decimal(str(value)) / Decimal(str(self.quantity_step))
        whole = lots.to_integral_value(rounding=ROUND_DOWN)
        if not floor and lots != whole:
            raise ValueError("qty 不在quantity_step网格")
        result = float(whole * Decimal(str(self.quantity_step)))
        if opening and result < self.min_quantity:
            if floor:
                return 0.0
            raise ValueError("qty 小于min_quantity")
        return result

    def price(self, value, *, side=None) -> float:
        """请求价格严格校验；执行价格按不利方向规范化。"""
        value = finite(value, "price", positive=True)
        if self.price_tick is None:
            return value
        ticks = Decimal(str(value)) / Decimal(str(self.price_tick))
        rounded = ticks.to_integral_value(rounding=ROUND_CEILING if side == "buy" else ROUND_FLOOR)
        if side is None and ticks != rounded:
            raise ValueError("price 不在price_tick网格")
        return float(rounded * Decimal(str(self.price_tick)))

    def validate_data(self, frame):
        """交易行情必须有序、唯一且价格有效，显式tick不得静默修正。"""
        if not frame.index.is_monotonic_increasing or not frame.index.is_unique:
            raise ValueError("行情索引必须递增且唯一")
        values = frame[["Open", "High", "Low", "Close"]].to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError("OHLC必须为有限正价")
        if self.price_tick is not None:
            for price in np.unique(values):
                self.price(float(price))

    def round_price_to_tick(self, value: float) -> float:
        """按显式 tick 就近归整价格，半 tick 向较高价格归整。

        Args:
            value: 有限正价格，不接受布尔值。

        Returns:
            通过本品种严格网格校验的有限正 float；不改变撮合舍入政策。

        Raises:
            TypeError: value 不是数值或为布尔值。
            ValueError: 缺少 tick、输入非法、结果为零或无法以 float 表示合法网格。
        """
        value = finite(value, "price", positive=True)
        if self.price_tick is None:
            raise ValueError("round_price_to_tick 要求显式 price_tick")
        # 两个有限 float 的十进制指数差可超过 600；避免默认精度吞掉半 tick。
        with localcontext() as context:
            context.prec = 700
            tick = Decimal(str(self.price_tick))
            ticks = (Decimal(str(value)) / tick).to_integral_value(rounding=ROUND_HALF_UP)
            exact = ticks * tick
            result = float(exact)
            if Decimal(str(result)) != exact:
                raise ValueError("归整价格不能以 float 精确表示网格")
            return self.price(result)
