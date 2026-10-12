"""旧 parallel 路径的兼容导出；实现位于 backtest.parallel。"""

from openbacktesting.simulation.parallel import (
    SharedMemory,
    SharedMemoryManager,
    _batch,  # noqa: F401 — 旧入口重导出
)

__all__ = ["SharedMemory", "SharedMemoryManager"]
