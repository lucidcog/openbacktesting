"""方法式指标入口的轻量适配；计算与登记仍由策略负责。"""

from collections.abc import Callable, Mapping, Sequence

from .predicates import CrossPredicates
from .types import IndicatorError, IndicatorHandle

Source = str | IndicatorHandle
Inputs = Mapping[str, Source]


class IndicatorResult:
    """多输出的只读属性容器；通道视图只在初始化时创建。"""

    __slots__ = ("_channels", "_handle")

    def __init__(self, handle: IndicatorHandle):
        self._handle = handle
        self._channels = {name: handle[name] for name in handle.name}

    def __getitem__(self, name: str) -> IndicatorHandle:
        return self._channels[name]

    @property
    def ready(self):
        """各输出共享的最低历史条件掩码。"""
        return self._handle.ready

    @property
    def valid(self):
        """底层各通道的有效性掩码；交易前优先检查所选通道。"""
        return self._handle.valid

    @property
    def metadata(self):
        """返回底层句柄来源元数据的独立副本。"""
        return self._handle.metadata

    @property
    def df(self):
        """返回全部通道当前前缀的 pandas DataFrame 副本。"""
        return self._handle.df


class IndicatorNamespace(CrossPredicates):
    """绑定单个策略的登记回调，避免指标层反向依赖策略实现。"""

    def __init__(self, register: Callable[..., IndicatorHandle]):
        self._register = register

    def _call(
        self,
        indicator: str,
        primary: str,
        source: Source | None,
        inputs: Inputs | None,
        backend: str | None,
        required_outputs: Sequence[str] | None,
        parameters: dict,
    ) -> IndicatorHandle:
        if source is not None:
            if inputs is not None:
                raise IndicatorError(
                    "invalid-parameter", indicator, "source 与 inputs 不能同时指定"
                )
            if not isinstance(source, (str, IndicatorHandle)):
                raise IndicatorError(
                    "missing-input", indicator, "source 须为列名或单通道句柄；多输出请先选择通道"
                )
            inputs = {primary: source}
        return self._register(
            indicator,
            inputs=inputs,
            backend=backend,
            required_outputs=required_outputs,
            **parameters,
        )

    def _call_inputs(
        self,
        indicator: str,
        sources: dict[str, Source | None],
        inputs: Inputs | None,
        backend: str | None,
        required_outputs: Sequence[str] | None,
        parameters: dict,
    ) -> IndicatorHandle:
        bound = {name: source for name, source in sources.items() if source is not None}
        if bound and inputs is not None:
            raise IndicatorError("invalid-parameter", indicator, "具名输入与 inputs 不能同时指定")
        return self._register(
            indicator,
            inputs=bound if bound else inputs,
            backend=backend,
            required_outputs=required_outputs,
            **parameters,
        )
