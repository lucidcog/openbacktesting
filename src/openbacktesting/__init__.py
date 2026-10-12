"""OpenBacktesting native historical backtesting kernel."""

import sys as _sys

__version__ = "0.2.0"

from . import colors, indicators, inputs, lib, runtime  # noqa: F401
from .colors import Color as Color
from .data.context import DataContext as DataContext
from .data.timeframe import Timeframe as Timeframe
from .data.timeframe import TimeframeUnit as TimeframeUnit
from .engine import Backtest as Backtest
from .engine import Strategy as Strategy
from .logs import RunLogs as RunLogs
from .simulation.config import CommissionType as CommissionType
from .simulation.config import DefaultOrderSize as DefaultOrderSize
from .simulation.config import EndPolicy as EndPolicy
from .simulation.config import ExecutionTiming as ExecutionTiming
from .simulation.config import QuantityType as QuantityType
from .simulation.config import SlippageType as SlippageType
from .strategy.bar_state import BarState as BarState
from .strategy.declaration import backtest as backtest
from .util import try_

# Skip Pool in pdoc3 API docs. Interested users get the warning.
__pdoc__ = {"openbacktesting.Pool": False}


# Add overridable openbacktesting.Pool used for parallel optimization
def Pool(processes=None, initializer=None, initargs=()):
    """Create an optimization execution pool; spawn uses a thread pool by default. Advanced callers may override this entry point; multiprocessing calls require a main guard."""
    import multiprocessing as mp
    import sys

    # Revert performance related change in Python>=3.14
    if sys.platform.startswith("linux") and mp.get_start_method(allow_none=True) != "fork":
        try_(lambda: mp.set_start_method("fork"))
    if mp.get_start_method() == "spawn":
        import warnings

        warnings.warn(
            "If you want to use multi-process optimization with "
            "`multiprocessing.get_start_method() == 'spawn'` (e.g. on Windows),"
            "set `openbacktesting.Pool = multiprocessing.Pool` (or of the desired context) "
            "and hide `bt.optimize()` call behind a `if __name__ == '__main__'` guard. "
            "Currently using thread-based paralellism, "
            "which might be slightly slower for non-numpy / non-GIL-releasing code. "
            "See README.md",
            category=RuntimeWarning,
            stacklevel=3,
        )
        from multiprocessing.dummy import Pool

        return Pool(processes, initializer, initargs)
    else:
        return mp.Pool(processes, initializer, initargs)


from . import (  # noqa: F401
    aggregation,
    broker,
    data,
    helpers,
    optimization,
    parallel,
    simulation,
    strategy,
    util,
)

# The old module path and new file share the same objects, preserving imports, patching, and pickle lookup.
for _module_name in (
    "aggregation",
    "broker",
    "data",
    "helpers",
    "optimization",
    "parallel",
    "strategy",
    "util",
):
    _module = _sys.modules[f"{__name__}.{_module_name}"]
    globals()[f"_{_module_name}"] = _module
    _sys.modules[f"{__name__}._{_module_name}"] = _module
del _module_name, _module
