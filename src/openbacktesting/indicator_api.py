"""旧类型路径的兼容导出；实现位于 indicators 子包。"""

from .indicators.api import (
    IndicatorNamespace,
    IndicatorResult,
    Inputs,
    Source,
)

__all__ = ["IndicatorNamespace", "IndicatorResult", "Inputs", "Source"]
