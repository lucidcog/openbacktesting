"""独立的确定性OHLC成交价格政策。"""

from dataclasses import dataclass

from openbacktesting.broker.models import finite


@dataclass(frozen=True)
class Slippage:
    """无滑点、固定金额或基点滑点；每次成交只应用一次。"""

    mode: str = "none"
    value: float = 0

    def __post_init__(self):
        if self.mode not in ("none", "fixed", "bps"):
            raise ValueError("slippage模式必须为none/fixed/bps")
        object.__setattr__(self, "value", finite(self.value, "slippage"))
        if self.value < 0 or (self.mode == "none" and self.value != 0):
            raise ValueError("slippage值不合法")

    def cost(self, price: float) -> float:
        """返回非负单单位滑点距离。"""
        if self.mode == "fixed":
            return self.value
        return price * self.value / 10000 if self.mode == "bps" else 0.0


def match_price(request, *, triggered, open_, high, low):
    """返回候选基准价及触发状态，不修改请求。"""
    buy = request.side == "buy"
    stop = request.stop if not triggered else None
    if stop is not None:
        if not (high >= stop if buy else low <= stop):
            return None, False
        triggered = True
    if request.limit is not None:
        limit = request.limit
        if not (low <= limit if buy else high >= limit):
            return None, triggered
        if stop is not None and (limit <= stop if buy else limit >= stop):
            return None, triggered
        return (min(stop or open_, limit) if buy else max(stop or open_, limit)), triggered
    return ((max(open_, stop) if buy else min(open_, stop)) if stop else open_), triggered


def execution_price(base, side, *, spread, slippage, instrument, limit, bounds=None):
    """先应用成本和网格，再检查限价；普通执行约束于OHLC范围。"""
    sign = 1 if side == "buy" else -1
    price = base * (1 + sign * spread) + sign * slippage.cost(base)
    price = instrument.price(price, side=side)
    if limit is not None and (price > limit if side == "buy" else price < limit):
        return None
    if bounds is not None:
        low, high = bounds
        price = min(max(price, low), high)
        price = instrument.price(price, side=side)
        if not low <= price <= high:
            return None
    if limit is not None and (price > limit if side == "buy" else price < limit):
        return None
    return price
