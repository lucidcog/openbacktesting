"""原生内核旧路径兼容入口；定义位于对应职责模块。"""

from openbacktesting.broker.core import (
    Order,
    Position,
    Trade,
    __pdoc__,  # noqa: F401 — 保留原路径兼容导出
    _Broker,  # noqa: F401 — 保留原路径兼容导出
    _OutOfMoneyError,  # noqa: F401 — 保留原路径兼容导出
)
from openbacktesting.data.core import (
    _Data,  # noqa: F401 — 保留原路径兼容导出
    _Indicator,  # noqa: F401 — 保留原路径兼容导出
    _indicator_warmup_nbars,  # noqa: F401 — 保留原路径兼容导出
    _strategy_indicators,  # noqa: F401 — 保留原路径兼容导出
)
from openbacktesting.helpers import (
    _as_str,  # noqa: F401 — 保留原路径兼容导出
    patch,  # noqa: F401 — 保留原路径兼容导出
    try_,  # noqa: F401 — 保留原路径兼容导出
)
from openbacktesting.portfolio.stats import (
    compute_stats,  # noqa: F401 — 保留原路径兼容导出
    dummy_stats,  # noqa: F401 — 保留原路径兼容导出
)
from openbacktesting.simulation.core import Backtest
from openbacktesting.simulation.parallel import (
    SharedMemoryManager,  # noqa: F401 — 保留原路径兼容导出
    _batch,  # noqa: F401 — 保留原路径兼容导出
)
from openbacktesting.strategy.base import Strategy
from openbacktesting.util import _tqdm  # noqa: F401 — 保留原路径兼容导出

__all__ = ["Strategy", "Position", "Order", "Trade", "Backtest"]  # noqa: RUF022 — 保持原公开导出顺序
