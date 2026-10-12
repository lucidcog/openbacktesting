"""旧 optimization 路径的兼容导出；实现位于 backtest.optimization。"""

from openbacktesting.simulation.optimization import (
    _joined_pool,  # noqa: F401 — 旧入口重导出
    _optimize,  # noqa: F401 — 旧入口重导出
)

__all__ = []
