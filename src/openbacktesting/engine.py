"""Compatibility entry point for old native-kernel paths; definitions reside in the corresponding responsibility modules."""

from openbacktesting.broker.core import (
    Order,
    Position,
    Trade,
    __pdoc__,  # noqa: F401 — preserve compatibility exports at the original path
    _Broker,  # noqa: F401 — preserve compatibility exports at the original path
    _OutOfMoneyError,  # noqa: F401 — preserve compatibility exports at the original path
)
from openbacktesting.data.core import (
    _Data,  # noqa: F401 — preserve compatibility exports at the original path
    _Indicator,  # noqa: F401 — preserve compatibility exports at the original path
    _indicator_warmup_nbars,  # noqa: F401 — preserve compatibility exports at the original path
    _strategy_indicators,  # noqa: F401 — preserve compatibility exports at the original path
)
from openbacktesting.helpers import (
    _as_str,  # noqa: F401 — preserve compatibility exports at the original path
    patch,  # noqa: F401 — preserve compatibility exports at the original path
    try_,  # noqa: F401 — preserve compatibility exports at the original path
)
from openbacktesting.portfolio.stats import (
    compute_stats,  # noqa: F401 — preserve compatibility exports at the original path
    dummy_stats,  # noqa: F401 — preserve compatibility exports at the original path
)
from openbacktesting.simulation.core import Backtest
from openbacktesting.simulation.parallel import (
    SharedMemoryManager,  # noqa: F401 — preserve compatibility exports at the original path
    _batch,  # noqa: F401 — preserve compatibility exports at the original path
)
from openbacktesting.strategy.base import Strategy
from openbacktesting.util import _tqdm  # noqa: F401 — preserve compatibility exports at the original path

__all__ = ["Strategy", "Position", "Order", "Trade", "Backtest"]  # noqa: RUF022 — preserve the original public export order
