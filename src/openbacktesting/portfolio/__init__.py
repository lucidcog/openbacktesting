"""单次回测的冻结账户、交易与报告数据。"""

from .snapshot import PortfolioSnapshot as PortfolioSnapshot
from .snapshot import export_result as export_result
from .snapshot import get_snapshot as get_snapshot

__all__ = ["PortfolioSnapshot", "export_result", "get_snapshot", "report_catalog"]


def report_catalog() -> dict:
    """返回报告字段目录的独立副本，供宿主核对覆盖与方法身份。"""
    import json
    from importlib.resources import files

    return json.loads(files(__package__).joinpath("catalog.json").read_text(encoding="utf-8"))
