"""模拟执行包的延迟类导出；实现位于 simulation.core。"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openbacktesting.simulation.core import Backtest as Backtest

__all__ = ["Backtest"]


def __getattr__(name):
    if name == "Backtest":
        from openbacktesting.simulation.core import Backtest

        globals()[name] = Backtest
        return Backtest
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
