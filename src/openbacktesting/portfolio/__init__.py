"""Frozen account, trading, and report data for a single backtest."""

from .snapshot import PortfolioSnapshot as PortfolioSnapshot
from .snapshot import export_result as export_result
from .snapshot import get_snapshot as get_snapshot

__all__ = ["PortfolioSnapshot", "export_result", "get_snapshot", "report_catalog"]


def report_catalog() -> dict:
    """Return an independent copy of the report-field catalog for hosts to check coverage and method identity."""
    import json
    from importlib.resources import files

    return json.loads(files(__package__).joinpath("catalog.json").read_text(encoding="utf-8"))
