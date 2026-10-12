"""内置指标公开入口；具体计算实现按类别维护。"""

from .runtime import DEFAULT_CACHE_BYTES as DEFAULT_CACHE_BYTES
from .runtime import IndicatorCache as IndicatorCache
from .runtime import catalog as catalog
from .runtime import compute as compute
from .runtime import describe as describe
