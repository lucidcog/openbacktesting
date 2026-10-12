"""消费成功加载的策略模块；发现无数据依赖，运行由宿主注入图表上下文。"""

from collections.abc import Mapping
from dataclasses import asdict
from importlib.metadata import version
from inspect import isabstract

import pandas as pd

from openbacktesting.broker.instrument import InstrumentSpec
from openbacktesting.data.context import DataContext
from openbacktesting.indicators.runtime import DEFAULT_CACHE_BYTES
from openbacktesting.logs import RunLogs
from openbacktesting.optimizer.query import ExperimentResult
from openbacktesting.plotting.types import PlottingLimits
from openbacktesting.simulation.collection import DEFAULT_COLLECTION, CollectionPolicy
from openbacktesting.simulation.core import Backtest
from openbacktesting.strategy.base import Strategy
from openbacktesting.strategy.declaration import declaration
from openbacktesting.strategy.inputs import describe as describe_inputs
from openbacktesting.strategy.inputs import resolve_request


def discover(namespace: Mapping) -> type[Strategy]:
    """发现本模块直接装饰的唯一具体策略；别名去重，排除导入与继承入口。

    Args:
        namespace: 成功加载模块的命名空间，必须含非空字符串 __name__。

    Returns:
        type[Strategy]: 原策略类，不构造实例。

    Raises:
        TypeError: 命名空间或声明无效。
        ValueError: 没有或存在多个入口。
    """
    if not isinstance(namespace, Mapping):
        raise TypeError("namespace 必须为模块映射")
    name = namespace.get("__name__")
    if not isinstance(name, str) or not name:
        raise TypeError("namespace 必须包含非空 __name__")
    candidates = {}
    for value in namespace.values():
        if (
            isinstance(value, type)
            and issubclass(value, Strategy)
            and value.__module__ == name
            and not isabstract(value)
            and declaration(value) is not None
        ):
            candidates[id(value)] = value
    if len(candidates) != 1:
        names = sorted(f"{cls.__module__}:{cls.__qualname__}" for cls in candidates.values())
        raise ValueError(f"模块必须有且仅有一个 @backtest 策略；候选: {names}")
    return next(iter(candidates.values()))


def describe(namespace: Mapping) -> dict:
    """无行情导出 inputs 及完整默认回测设置，不执行策略生命周期。

    返回的 backtest 描述独立于 input schemaHash；修改副本不修改类声明。
    """
    cls = discover(namespace)
    settings = declaration(cls)
    return describe_inputs(cls) | {
        "backtest": {"schemaVersion": 2, "settings": settings.snapshot()}
    }


def run(
    namespace: Mapping,
    request: Mapping | None = None,
    *,
    data: pd.DataFrame,
    context: DataContext,
    instrument: InstrumentSpec,
    settings: Mapping | None = None,
    options: Mapping | None = None,
    logs: RunLogs | None = None,
) -> pd.Series:
    """按本次图表运行新会话，返回既有结果及 backtest_snapshot。

    Args:
        namespace: 宿主本次成功加载的模块；不再接受 bt-only 导出。
        request: 既有按标题的输入请求；None 使用默认参数。
        data: 当前图表 OHLC，必须具有带时区的 DatetimeIndex。
        context: 实际周期及图表、策略日历和统计共用的时区。
            在策略构造前转换内部索引，保留输入与绝对时刻，不触发重采样。
            改变时区需重新运行，当地时间条件及统计分日结果允许变化。
        instrument: 图表品种规格，不从行情推断。
        settings: 平铺设置的稀疏覆盖；枚举字段接受对应成员或精确字符串。
            切换类型必须同时给数值，default_qty_value=None 清除默认数量。
        options: 缓存预算、plotting 和 plotting_limits，属于宿主运行选项。
        logs: 可选的宿主日志会话，成功或异常后均可 get_logs，顺序重用清空旧记录。

    不加载源码、不缓存旧实例、不修改声明；异常原样传播。
    """
    if logs is not None and not isinstance(logs, RunLogs):
        raise TypeError("logs 必须为 RunLogs 或 None")
    session = RunLogs() if logs is None else logs
    with session._capture():
        return _run(namespace, request, data, context, instrument, settings, options, session)


def _run(
    namespace,
    request,
    data,
    context,
    instrument,
    settings,
    options,
    session,
    collection=DEFAULT_COLLECTION,
):
    cls = discover(namespace)
    resolved = declaration(cls).resolve(settings)
    if not isinstance(context, DataContext):
        raise TypeError("context 必须为 DataContext")
    if not isinstance(instrument, InstrumentSpec):
        raise TypeError("instrument 必须为 InstrumentSpec")
    if options is None:
        options = {}
    if not isinstance(options, Mapping):
        raise TypeError("options 必须为映射或 None")
    defaults = {
        "indicator_cache_bytes": DEFAULT_CACHE_BYTES,
        "plotting": True,
        "plotting_limits": PlottingLimits(),
    }
    unknown = set(options).difference(defaults)
    if unknown:
        raise ValueError(f"未知运行选项: {list(unknown)!r}")
    effective_options = defaults | dict(options)
    if effective_options["plotting_limits"] is None:
        effective_options["plotting_limits"] = PlottingLimits()
    # 摘要和值错误必须在任何策略构造之前暴露，保持既有标题入口语义。
    if request is not None:
        resolve_request(cls, request)
    bt = Backtest(
        data,
        cls,
        context=context,
        instrument=instrument,
        _collection=collection,
        **resolved.kwargs(),
        **effective_options,
    )
    try:
        result = bt.run() if request is None else bt.run_inputs(request)
    finally:
        session._collector = bt._log_collector
    result.attrs["backtest_snapshot"] = {
        "schemaVersion": 2,
        "strategy": {"module": cls.__module__, "qualname": cls.__qualname__},
        "settings": resolved.snapshot(),
        "context": context.snapshot(),
        "instrument": asdict(instrument),
        "options": effective_options
        | {"plotting_limits": asdict(effective_options["plotting_limits"])},
        "engineVersion": version("openbacktesting"),
    }
    from openbacktesting.portfolio.snapshot import refresh_snapshot

    refresh_snapshot(result)
    return result


def optimize(
    namespace: Mapping,
    search: Mapping,
    *,
    path,
    identity,
    data: pd.DataFrame,
    context: DataContext,
    instrument: InstrumentSpec,
    request=None,
    settings=None,
    constraint=None,
    constraint_id=None,
    cancel=None,
    on_progress=None,
) -> ExperimentResult:
    """串行穷举选定 inputs，将每份完整 Portfolio 提交到新本地结果库。

    未选值来自当前 request；仅保留 Portfolio，不采集日志/绘图。
    identity 是宿主提供的 ExecutionIdentity；数据/配置身份由框架计算。
    constraint 使用完整 wire 值并需 constraint_id；cancel 为无参 callable。
    返回只读 ExperimentResult；策略失败组记错误后继续，存储失败停止。
    """
    return _optimize(
        namespace,
        search,
        path,
        identity,
        data,
        context,
        instrument,
        request,
        settings,
        constraint,
        constraint_id,
        cancel,
        on_progress,
        None,
    )


def resume_optimization(
    namespace: Mapping,
    *,
    path,
    experiment_id: str,
    identity,
    data: pd.DataFrame,
    context: DataContext,
    instrument: InstrumentSpec,
    request=None,
    settings=None,
    constraint=None,
    constraint_id=None,
    cancel=None,
    on_progress=None,
) -> ExperimentResult:
    """核验当前声明、输入与执行身份后恢复未完成试验；不自动重试失败组。"""
    from openbacktesting.optimizer.models import Range, Values
    from openbacktesting.optimizer.query import open_result

    source = open_result(path, experiment_id).info()["plan"]
    search = {}
    for dimension in source["dimensions"]:
        expression = dimension["expression"]
        search[dimension["title"]] = (
            Range(**expression["range"]) if "range" in expression else Values(expression["values"])
        )
    return _optimize(
        namespace,
        search,
        path,
        identity,
        data,
        context,
        instrument,
        request,
        settings,
        constraint,
        constraint_id,
        cancel,
        on_progress,
        experiment_id,
    )


def _optimize(
    namespace,
    search,
    path,
    identity,
    data,
    context,
    instrument,
    request,
    settings,
    constraint,
    constraint_id,
    cancel,
    on_progress,
    experiment_id,
):
    from copy import deepcopy

    from openbacktesting.optimizer.identity import execution_identity
    from openbacktesting.optimizer.models import _ExportError
    from openbacktesting.optimizer.plan import plan
    from openbacktesting.optimizer.runner import execute
    from openbacktesting.portfolio.snapshot import export_result

    cls = discover(namespace)
    resolved = declaration(cls).resolve(settings)
    if not isinstance(context, DataContext) or not isinstance(instrument, InstrumentSpec):
        raise TypeError("optimizer: 必须提供 DataContext 和 InstrumentSpec")
    frozen = data.copy(deep=True)
    run_settings = resolved.snapshot()
    backtest = {
        "schemaVersion": 2,
        "settings": run_settings,
        "context": context.snapshot(),
        "instrument": asdict(instrument),
        "engineVersion": version("openbacktesting"),
    }
    execution = execution_identity(frozen, identity, backtest)
    plan_value = plan(
        cls, search, base_inputs=request, execution=execution, constraint_id=constraint_id
    )
    # 构造校验不执行策略；必须在新建结果库及第一组之前拒绝无效行情。
    Backtest(
        frozen, cls, context=context, instrument=instrument, **resolved.kwargs(), plotting=False
    )
    namespace = dict(namespace)
    collection = CollectionPolicy(portfolio=True, logs=False, plotting=False)

    def run_one(inputs_request):
        session = RunLogs()
        with session._capture():
            result = _run(
                namespace,
                inputs_request,
                frozen,
                context,
                instrument,
                deepcopy(run_settings),
                {"plotting": False},
                session,
                collection,
            )
        try:
            return export_result(result)
        except Exception as error:
            raise _ExportError(str(error)) from error

    return execute(
        plan_value,
        run_one,
        path,
        experiment_id=experiment_id,
        constraint=constraint,
        cancel=cancel,
        on_progress=on_progress,
    )
