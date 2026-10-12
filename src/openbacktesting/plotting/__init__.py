"""独立绘图数据接口；不包含绘图后端、文件输出或浏览器操作。"""

from openbacktesting.plotting.collector import Plotting
from openbacktesting.plotting.encoding import export_result
from openbacktesting.plotting.types import (
    FillRef,
    MarkerRef,
    PaneRef,
    PlotRef,
    PlottingError,
    PlottingLimits,
)

__all__ = [
    "FillRef",
    "MarkerRef",
    "PaneRef",
    "PlotRef",
    "Plotting",
    "PlottingError",
    "PlottingLimits",
    "export_result",
]
