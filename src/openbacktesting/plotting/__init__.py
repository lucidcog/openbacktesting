"""Standalone plotting-data interface without rendering backends, file output, or browser operations."""

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
