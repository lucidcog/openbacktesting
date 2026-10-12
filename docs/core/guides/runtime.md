# 宿主接管与优化

需要保留每组完整结果时使用[参数实验与本地 Portfolio](optimizer.md)中的 `runtime.optimize()`；它独立于下文返回最佳评分的 `Backtest.optimize()`。

## 框架代码：发现与运行

作者通过 `@backtest(...)` 声明策略设置，框架负责当前图表数据、上下文和品种规格。以下都是框架代码；`namespace` 是宿主本次成功加载用户模块后的全局映射。core 不加载源码，也不提供桌面运行器。

```python
from openbacktesting import DataContext, Timeframe, runtime

strategy = runtime.discover(namespace)
schema = runtime.describe(namespace)
request = {
    "schemaVersion": schema["schemaVersion"],
    "schemaHash": schema["schemaHash"],
    "values": {"均线周期": 30},
}
result = runtime.run(
    namespace,
    request,  # 针对参数指南中的 ConfigurableSma；省略时使用默认值
    data=chart_data,
    context=DataContext(Timeframe.minutes(15), "Asia/Shanghai"),
    instrument=chart_instrument,
    settings={"cash": 20_000},
    options={"plotting": True},
)
snapshot = result.attrs["input_snapshot"]
```

`chart_data`、真实周期/时区和 `chart_instrument` 均由宿主从本次图表提供，不能复制示例常量假定用户正在查看 15 分钟图。完整离线配方见[图表上下文示例](../../../examples/advanced/chart_context.py)，展示两套品种/周期、图表当地小时条件、统计日界和夏令时重复小时。

| 责任                   | 用户代码                          | 框架代码                             |
| ---------------------- | --------------------------------- | ------------------------------------ |
| 策略逻辑与参数         | `Strategy`、`inputs`、`init/next` | 发现参数并保留标题请求               |
| 默认回测设置           | `@backtest(...)`                  | 以 `settings` 稀疏覆盖本次有效值     |
| 数据、周期、时区与品种 | 不声明                            | 注入 `data/context/instrument`       |
| 缓存与绘图预算         | 不声明                            | `options`                            |
| 运行与结果             | 不调用执行 API                    | 构造新的 `Backtest` 并执行、保存快照 |

发现要求 namespace 是含非空 `__name__` 的映射，且存在唯一的本模块直接装饰、非抽象 `Strategy` 类。类的多个别名去重，导入类和未直接装饰的派生类不算入口；零个或多个入口报错。装饰器返回原类，不使用全局注册表。`discover/describe` 不需要数据，不执行构造、init 或 next；只导出旧 bt 的脚本不再是 runtime 入口。

`schema["backtest"]` 使用 `schemaVersion=2`，settings 完整列出 [16 个平铺字段](author.md#平铺回测设置)。五类枚举导出为精确小写字符串，佣金和权益数量保留作者百分数单位；不导出嵌套模型。

宿主 `settings` 接受稀疏映射，分类字段可传对应枚举或表中精确字符串，拒绝大写、空白、错误枚举、旧字段和对象。未覆盖字段保留声明值；`default_qty_value=None` 清空默认数量，`max_gross_exposure=None` 清空暴露上限。三组 type/value 参数遵守同一规则：只改 value 沿用类型；重复相同 type 可不带值；改为不同 type 必须同时给 value，包括 0 或合法的 None。整份设置在构造策略前解码和校验，失败不会部分应用或修改原声明。

宿主保存／读取配置封套时必须先验证版本 2，拒绝版本 1 和未知版本，再使用 settings；不要把旧数值自动解释成新百分数。可运行的 `read_settings` 及拒绝断言见[宿主教程](../../../examples/advanced/strategy_settings.py)。内部不可变 BacktestSettings 的 snapshot/from_snapshot 用于完整 16 字段 JSON 往返，恢复拒绝缺失／未知字段、嵌套对象及 Python 枚举；稀疏覆盖则走 runtime。

运行选项仅接受 `indicator_cache_bytes/plotting/plotting_limits`，不混入作者默认设置。`settings/options` 只作用于本次会话，不修改类声明。原生 `Backtest(data, StrategyClass, ...)` 保持显式配置，不自动合并装饰器；原生优化或回测变体继续由高级宿主自行构造调用。

## 周期与上下文

`TimeframeUnit` 是字符串枚举：`SECOND/MINUTE/DAY/WEEK/MONTH`。`Timeframe(unit, multiplier)` 不可变且可哈希；倍数须为严格正整数，拒绝 bool、浮点与字符串。可用 `seconds/minutes/hours/days/weeks/months` 六个便利构造；小时规范化成分钟，日、周、月保留日历单位，`days(7) != weeks(1)`。不使用固定 Enum 列举所有倍数，也不提供 Pine 周期字符串解析或秒数换算。

`DataContext(timeframe, timezone)` 不可变，时区使用有效的 IANA 标识，推荐 `UTC` 或 `America/New_York` 等地区名称。runtime 必须接收它和显式 `InstrumentSpec`，并要求行情使用带时区的 `DatetimeIndex`。宿主统一提供 UTC 数据；内核也兼容其他带时区输入，在策略构造和 init 前于副本上转换索引，保持绝对时刻、OHLCV 和休市缺口。不猜测周期、不本地化未知时区，也不自动重采样；无时区输入在带 context 路径中拒绝。

本次 `timezone` 同时用于图表、策略日历判断和统计分组。三个策略索引入口直接提供图表时区，用户不必手动换算。图表改时区后，宿主应以新 context 重新运行；原结果仍属于旧快照。时间条件策略的交易及统计均可能改变，无时间条件策略的权益可相同而年化指标不同，详见[统计口径](results.md#统计基准与重算)。周期不改变当前年化推断算法，图表自然日也不等于交易所交易日。

共享内存按绝对时刻和原精度传递时间，再恢复图表时区，夏令时回拨的同名小时保留不同偏移。绘图轴继续输出 UTC 纳秒标签与时区元信息，不给 UNIX 时间戳人为加偏移；桌面消费与切换时区联动尚未接入。

策略在构造后的 `init` 和 `next` 通过只读 `self.timeframe` 读取实际周期；类字段、params、inputs、赋值或删除均不能覆盖。低层 `Backtest` 的 `context` 可省略，此时 `self.timeframe is None`，保留旧数据入口行为。

## 参数与结果快照

原有输入摘要仅描述 inputs，修改回测设置不会改变 `schemaHash`。请求在策略构造前校验；只有 request 为 None 才使用默认值，空字典不被忽略。无 inputs 的策略描述仍为空；向它提交标题请求会被拒绝。异常原样传播。

统计、交易、指标与绘图结果保持原出口。`result.attrs["backtest_snapshot"]` 以 `schemaVersion=2` 独立记录策略 module/qualname、解析后的全部设置、图表上下文、品种、运行选项和 core 版本，表示为纯 JSON 值；它不包含代码摘要或完整行情。带 inputs 的策略仍有独立 `input_snapshot`。修改描述或请求副本不会修改类声明和已有结果。

宿主每次加载失败就停止，不回退到上一轮 namespace；runtime 不缓存策略实例。宿主负责源码身份、输入配置归属和代码执行边界。模块加载会执行用户顶层 Python，发现 API 和 Worker 都不是系统沙箱。

## 框架代码：优化与结果消费

优化与结果消费也由宿主调用。下面片段直接引用原生优化教程的 main；完整文件定义了 Sma4Cross、周期约束和显式执行入口，见[统一示例](../examples.md)。

[完整源码](../../../examples/advanced/parameter_optimization.py)

默认 grid 搜索；`method="sambo"` 需要安装优化 extra。跨进程入口放在 `if __name__ == "__main__"` 内，遵循 Python 的启动方式要求。平台默认采用 spawn 时，内核会提示并使用线程池；高级调用方可显式覆盖 `openbacktesting.Pool`。不同平台性能与启动行为不能视为一致。

内核返回统计、`_trades` 交易明细和 `_equity_curve` 权益数据；`return_heatmap=True` 返回参数评分表，不生成图表。示例统一从 [examples/README.md](../../../examples/README.md) 选择：`strategies/` 是推荐作者模板，`advanced/` 包含自定义作者例与显式执行的原生教程，类别由索引标明。新增 core 功能必须同批补充或更新可运行示例、索引与验证。示例随源码和 sdist 分发，wheel 不包含；机器学习教程需 test extra 且标为非推荐研究。

新字段随默认描述和有效运行快照导出，仍不参与 input schemaHash。`risk_free_rate` 默认为零、范围 (-1,1)，0.02 表示年化 2%；它不进入交易账户。枚举及内部有效配置可 pickle；内部适配仅在进入原生 Backtest 前将佣金／权益百分数除以 100，复用 Commission、DefaultOrderSize 与 Slippage。原生 Backtest/优化保持原单位和高级模型入口，不自动读取装饰器。参见[统计基准](results.md#统计基准与重算)与[运行示例](../../../examples/advanced/strategy_settings.py)。

## 宿主在失败后取回日志

从根包导入 `RunLogs`，将会话作为独立关键字传入 `runtime.run(..., logs=session)`，随后 `session.get_logs()` 可读取成功或失败前的已写记录。运行依然返回 Series，异常保持原对象；会话不放入 settings/options。不传会话时成功结果仍有 `attrs["strategy_logs"]`，失败没有额外公开日志出口。

顺序复用会话会在策略发现与请求验证前清空旧记录；同时复用或重入抛 RuntimeError，且不清空活动运行；错误类型抛 TypeError。会话退出后可重用，旧返回副本不变。以下受测教程演示低层与宿主的异常取回及位置字段：

[完整源码](../../../examples/advanced/strategy_logs.py)

grid 与 SAMBO 候选不采集日志，仅最终正式重跑采集；无交易回退也视为正式重跑。搜索失败返回空日志，最终重跑失败保留该次记录。候选仍校验消息类型，并正常求值 f-string 等表达式，不能依赖候选日志评分。MultiBacktest 保持统计汇总接口，不提供跨数据集日志合流。字段与容量边界见[日志结果](results.md#策略日志)。

## 消费Portfolio

成功出口可调用`openbacktesting.portfolio.export_result(result)`获取完整严格JSON字典；它与plotting的同名函数分属独立模块。报告无需策略活对象，包含原运行配置和有效统计利率；只在宿主明确需要时持久化或传输。Portfolio独立合同不改变Worker的RunResult或strategy.execute能力，当前没有网页或桌面回测接入。见[结果口径](results.md#portfolio-完整报告)。
