# 回测与策略

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

作者通过 backtest 声明策略默认设置；宿主构造 Backtest 并执行，Strategy 定义初始化与逐步交易逻辑。

[使用指南](../quickstart.md) · [兼容与内部入口](classification.md)

<a id="openbacktesting-backtest"></a>

## Backtest

完整对象：`openbacktesting.Backtest`

```python
openbacktesting.Backtest(data: 'pd.DataFrame', strategy: 'type[Strategy]', *, cash: 'float' = 10000, spread: 'float' = 0.0, commission: 'float | tuple[float, float] | Commission | Callable[[float, float], float]' = 0.0, risk_free_rate: 'float' = 0.0, default_order_size: 'DefaultOrderSize | None' = None, margin: 'float' = 1.0, execution_timing='next_open', instrument=None, slippage=None, allow_short=True, max_gross_exposure=None, hedging=False, exclusive_orders=False, end_policy='mark_to_market', indicator_cache_bytes=67108864, context: 'DataContext | None' = None, plotting: 'bool' = True, plotting_limits: 'PlottingLimits | None' = None, _collection: 'CollectionPolicy' = CollectionPolicy(portfolio=True, logs=True, plotting=True))
```

保存单资产历史行情、策略及线性保证金账户配置。

data的OHLC必须为有限正价，索引有序且唯一。instrument明确数量步长和可选价格网格。
cash为初始余额；margin为名义保证金比例；hedging控制是否保留双向批次。
commission可为比例、(固定额, 比例)、Commission或纯费用函数，按每次实际执行收取一次。
spread及slippage作用于每次买卖执行；滑点不会允许订单越过限价。
execution_timing支持next_open或same_close；end_policy支持mark_to_market或close_at_last_close。
allow_short控制新增空头，max_gross_exposure是总名义/权益上限；合法减仓始终允许。
exclusive_orders在新普通订单提交时取消旧入场并提交现有批次退出。
context可选；提供时要求带时区索引并在副本上转换显示时区，策略可读self.timeframe。
risk_free_rate为年化小数，仅影响统计；default_order_size提供省略qty时的请求预算。
底层构造不自动合并@backtest设置，声明接管由runtime负责。
不支持旧size比例猜测、价格缩放、跨币种、成交量部分成交或实盘执行。

源码：`src/openbacktesting/simulation/core.py`。

<a id="openbacktesting-backtest-optimize"></a>

### optimize

完整对象：`openbacktesting.Backtest.optimize`

```python
openbacktesting.Backtest.optimize(self, *, maximize: 'str | Callable[[pd.Series], float]' = 'SQN', method: 'str' = 'grid', max_tries: 'float | None' = None, constraint: 'Callable[[dict], bool] | None' = None, return_heatmap: 'bool' = False, return_optimization: 'bool' = False, random_state: 'int | None' = None, **kwargs) -> 'pd.Series | tuple[pd.Series, pd.Series] | tuple[pd.Series, pd.Series, dict]'
```

搜索策略参数组合并按指定统计项或评分函数选择结果。


Optimize strategy parameters to an optimal combination.
Returns result `pd.Series` of the best run.

`maximize` is a string key from the
`openbacktesting.engine.Backtest.run`-returned results series,
or a function that accepts this series object and returns a number;
the higher the better. By default, the method maximizes
Van Tharp's [System Quality Number](https://altpower.app/?q=System+Quality+Number).

`method` is the optimization method. Currently two methods are supported:

* `"grid"` which does an exhaustive (or randomized) search over the
  cartesian product of parameter combinations, and
* `"sambo"` which finds close-to-optimal strategy parameters using
  [model-based optimization], making at most `max_tries` evaluations.

[model-based optimization]: https://sambo-optimization.github.io

`max_tries` is the maximal number of strategy runs to perform.
If `method="grid"`, this results in randomized grid search.
If `max_tries` is a floating value between (0, 1], this sets the
number of runs to approximately that fraction of full grid space.
Alternatively, if integer, it denotes the absolute maximum number
of evaluations. If unspecified (default), grid search is exhaustive,
whereas for `method="sambo"`, `max_tries` is set to 200.

`constraint` is a function that accepts a dict-like object of
parameters (with values) and returns `True` when the combination
is admissible to test with. By default, any parameters combination
is considered admissible.

If `return_heatmap` is `True`, besides returning the result
series, an additional `pd.Series` is returned with a multiindex
of all admissible parameter combinations, which can be further
inspected as a table of parameter combinations and objective values.

If `return_optimization` is True and `method = 'sambo'`,
in addition to result series (and maybe heatmap), return raw
[`scipy.optimize.OptimizeResult`][OptimizeResult] for further
inspection by the caller.

[OptimizeResult]: https://sambo-optimization.github.io/doc/sambo/#sambo.OptimizeResult
[SAMBO]: https://sambo-optimization.github.io

If you want reproducible optimization results, set `random_state`
to a fixed integer random seed.

Additional keyword arguments represent strategy arguments with
list-like collections of possible values. For example, the following
code finds and returns the "best" of the 7 admissible (of the
9 possible) parameter combinations:

    best_stats = backtest.optimize(sma1=[5, 10, 15], sma2=[10, 20, 40],
                                   constraint=lambda p: p.sma1 < p.sma2)

源码：`src/openbacktesting/simulation/core.py`。

<a id="openbacktesting-backtest-run"></a>

### run

完整对象：`openbacktesting.Backtest.run`

```python
openbacktesting.Backtest.run(self, **kwargs) -> 'pd.Series'
```

按策略参数回测，返回统计Series、纯值账本表及可选诊断策略。

公开统计键：
Start, End, Duration, Exposure Time [%]
Equity Final [$], Equity Peak [$], Return [%], Buy & Hold Return [%]
Return (Ann.) [%], Volatility (Ann.) [%], CAGR [%], Sharpe Ratio
Sortino Ratio, Calmar Ratio, Alpha [%], Beta
Max. Drawdown [%], Avg. Drawdown [%], Max. Drawdown Duration, Avg. Drawdown Duration
# Trades, Win Rate [%], Best Trade [%], Worst Trade [%]
Avg. Trade [%], Max. Trade Duration, Avg. Trade Duration, Profit Factor
Expectancy [%], SQN, Kelly Criterion, Commissions [$]
# Closed Lots, _strategy, _equity_curve, _trades
_orders, _order_sizing, _order_events, _fills, _trade_allocations
_positions, _account_curve, _final_account, _open_trades

订单及成交事件不受指标NaN门控；next从首根逐根调用。
每个正常bar保留账户与总暴露，终止处理另记terminal快照。
结果attrs含交易政策版本、配置和输入快照；_strategy不是重建交易事实的必要条件。

源码：`src/openbacktesting/simulation/core.py`。

<a id="openbacktesting-backtest-run-inputs"></a>

### run_inputs

完整对象：`openbacktesting.Backtest.run_inputs`

```python
openbacktesting.Backtest.run_inputs(self, request) -> 'pd.Series'
```

按唯一 title 提交带 schemaVersion/schemaHash/values 的输入请求。

源码：`src/openbacktesting/simulation/core.py`。

<a id="openbacktesting-backtest-get-logs"></a>

### get_logs

完整对象：`openbacktesting.Backtest.get_logs`

```python
openbacktesting.Backtest.get_logs(self) -> 'list[dict[str, str | int | None]]'
```

返回本次运行全部策略日志的独立副本，尚未运行时为空。

失败保留已写记录；run/run_inputs/optimize 的新调用清空旧日志。
日志带时间、bar_index、源码文件和行号；默认全量保留，不静默截断。

源码：`src/openbacktesting/simulation/core.py`。

<a id="openbacktesting-pool"></a>

## Pool

完整对象：`openbacktesting.Pool`

```python
openbacktesting.Pool(processes=None, initializer=None, initargs=())
```

创建优化执行池；spawn 默认使用线程池。高级调用方可覆盖此入口，多进程调用须有 main 保护。

源码：`src/openbacktesting/__init__.py`。

<a id="openbacktesting-strategy"></a>

## Strategy

完整对象：`openbacktesting.Strategy`

```python
openbacktesting.Strategy(broker, data, params)
```

策略基类：在 init 登记指标，在 next 根据当前可见历史下单。


A trading strategy base class. Extend this class and
override methods
`openbacktesting.engine.Strategy.init` and
`openbacktesting.engine.Strategy.next` to define
your own strategy.

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-ind"></a>

### ind

完整对象：`openbacktesting.Strategy.ind`

```python
openbacktesting.Strategy.ind(self, func: 'Callable', *args, name=None, **kwargs) -> 'IndicatorHandle'
```

在初始化阶段批量计算自定义指标，返回随回测游标读取的只读句柄。

同一函数可按不同参数登记多次，也可供多个策略复用。每次登记均执行
函数，不共享自定义计算缓存；内置公式优先使用 ``self.ta``。
函数在 init 中接收完整历史，作者须保证计算只依赖当前及过去数据。

Args:
    func: 返回一维或二维 array-like 的计算函数，时间轴长度须等于行情。
        Series/DataFrame 的索引须与行情完全一致；数组按位置对齐。
    *args: 原样传给计算函数的位置参数。
    name: 展示名称或多输出的通道名称序列，序列长度须与通道数一致。
        默认由函数和参数组成，名称中的格式字段由计算参数填充。
    **kwargs: 原样传给计算函数的关键字参数。

Returns:
    只读 IndicatorHandle。具名通道可用 ``result['middle']`` 读取；
    ``np.asarray()``、``.s`` 和 ``.df`` 得到读取时的前缀快照。

Raises:
    IndicatorError: 非 init 阶段登记、行情来源已改变或 pandas 索引错位。
    TypeError: name 不是字符串或字符串序列。
    ValueError: 输出形状、长度或通道名称数量不匹配。
    RuntimeError: 用户函数计算失败，原异常保留为 cause。

Note:
    默认 ready 全真，valid 由有限值决定；next 从首根逐根执行，
    作者须自行检查历史长度和所用通道的 valid。指标无效不抑制回调。
    更复杂的输出掩码不是此入口的公开参数。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-buy"></a>

### buy

完整对象：`openbacktesting.Strategy.buy`

```python
openbacktesting.Strategy.buy(self, *, qty: 'float' = <_Unset.VALUE: 'omitted'>, amount: 'float' = <_Unset.VALUE: 'omitted'>, percent: 'float' = <_Unset.VALUE: 'omitted'>, limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order'
```

提交增量订单；qty/amount/percent 三选一，percent=20 表示权益20%。

全部省略时使用默认数量。金额为单币种名义预算，不含费用；
按请求时 Close 换算并冻结，成交时仍可能拒绝。只减仓须显式 qty。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-close"></a>

### close

完整对象：`openbacktesting.Strategy.close`

```python
openbacktesting.Strategy.close(self) -> 'IndicatorHandle'
```

当前运行的收盘价序列，可在 init 直接传给 self.ta。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-closed-trades"></a>

### closed_trades

完整对象：`openbacktesting.Strategy.closed_trades`

```python
openbacktesting.Strategy.closed_trades(self) -> 'tuple[Trade, ...]'
```

已完成的交易列表，供逐笔分析使用。

List of settled trades (see `Trade`).

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-data"></a>

### data

完整对象：`openbacktesting.Strategy.data`

```python
openbacktesting.Strategy.data(self) -> '_Data'
```

当前可见的原始行情访问入口；在 init 中可见全历史，next 中只可见当前前缀。


Price data, roughly as passed into
`openbacktesting.engine.Backtest.__init__`,
but with two significant exceptions:

* `data` is _not_ a DataFrame, but a custom structure
  that serves customized numpy arrays for reasons of performance
  and convenience. Besides OHLCV columns, `.index` and length,
  it offers `.pip` property, the smallest price unit of change.
* Within `openbacktesting.engine.Strategy.init`, `data` arrays
  are available in full length, as passed into
  `openbacktesting.engine.Backtest.__init__`
  (for precomputing indicators and such). However, within
  `openbacktesting.engine.Strategy.next`, `data` arrays are
  only as long as the current iteration, simulating gradual
  price point revelation. In each call of
  `openbacktesting.engine.Strategy.next` (iteratively called by
  `openbacktesting.engine.Backtest` internally),
  the last array value (e.g. `data.Close[-1]`)
  is always the **most recent** value.
* If you need data arrays (e.g. `data.Close`) to be indexed
  **Pandas series**, you can call their `.s` accessor
  (e.g. `data.Close.s`). If you need the whole of data
  as a **DataFrame**, use `.df` accessor (i.e. `data.df`).

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-df"></a>

### df

完整对象：`openbacktesting.Strategy.df`

```python
openbacktesting.Strategy.df(self) -> 'pd.DataFrame'
```

当前可见的原行情表；不承诺深拷贝或内容隔离。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-equity"></a>

### equity

完整对象：`openbacktesting.Strategy.equity`

```python
openbacktesting.Strategy.equity(self) -> 'float'
```

当前账户权益，包含现金和持仓价值。

Current account equity (cash plus assets).

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-high"></a>

### high

完整对象：`openbacktesting.Strategy.high`

```python
openbacktesting.Strategy.high(self) -> 'IndicatorHandle'
```

当前运行的最高价序列。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-hl2"></a>

### hl2

完整对象：`openbacktesting.Strategy.hl2`

```python
openbacktesting.Strategy.hl2(self) -> 'IndicatorHandle'
```

(High + Low) / 2，按运行惰性计算。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-hlc3"></a>

### hlc3

完整对象：`openbacktesting.Strategy.hlc3`

```python
openbacktesting.Strategy.hlc3(self) -> 'IndicatorHandle'
```

(High + Low + Close) / 3。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-hlcc4"></a>

### hlcc4

完整对象：`openbacktesting.Strategy.hlcc4`

```python
openbacktesting.Strategy.hlcc4(self) -> 'IndicatorHandle'
```

(High + Low + Close + Close) / 4，不包含 Open。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-init"></a>

### init

完整对象：`openbacktesting.Strategy.init`

```python
openbacktesting.Strategy.init(self)
```

策略初始化入口，用于预计算及登记指标；可以访问完整历史数据。


Initialize the strategy.
Override this method.
Declare indicators (with `openbacktesting.engine.Strategy.ind`).
Precompute what needs to be precomputed or can be precomputed
in a vectorized fashion before the strategy starts.

If you extend composable strategies from `openbacktesting.lib`,
make sure to call:

    super().init()

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-low"></a>

### low

完整对象：`openbacktesting.Strategy.low`

```python
openbacktesting.Strategy.low(self) -> 'IndicatorHandle'
```

当前运行的最低价序列。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-next"></a>

### next

完整对象：`openbacktesting.Strategy.next`

```python
openbacktesting.Strategy.next(self)
```

逐根策略回调，从输入第 0 根开始，每根正常到达的 bar 调用一次。

指标历史不足或无效也会调用；读取 [-2] 前检查长度，消费指标前检查 valid。
bar_index/bar_state 表示当前输入位置及冻结首尾状态。


Main strategy runtime method, called as each new
`openbacktesting.engine.Strategy.data`
instance (row; full candlestick bar) becomes available.
This is the main method where strategy decisions
upon data precomputed in `openbacktesting.engine.Strategy.init`
take place.

If you extend composable strategies from `openbacktesting.lib`,
make sure to call:

    super().next()

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-open"></a>

### open

完整对象：`openbacktesting.Strategy.open`

```python
openbacktesting.Strategy.open(self) -> 'IndicatorHandle'
```

当前运行的开盘价序列；[-1] 为当前值。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-orders"></a>

### orders

完整对象：`openbacktesting.Strategy.orders`

```python
openbacktesting.Strategy.orders(self) -> 'tuple[Order, ...]'
```

等待执行的订单列表，可对其中订单调用 cancel。

List of orders (see `Order`) waiting for execution.

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-pip"></a>

### pip

完整对象：`openbacktesting.Strategy.pip`

```python
openbacktesting.Strategy.pip(self) -> 'float'
```

沿用全样本小数位精度估计，不代表交易所最小步长。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-position"></a>

### position

完整对象：`openbacktesting.Strategy.position`

```python
openbacktesting.Strategy.position(self) -> 'Position'
```

当前净仓位汇总，可读取规模、盈亏或请求平仓。

Instance of `openbacktesting.engine.Position`.

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-sell"></a>

### sell

完整对象：`openbacktesting.Strategy.sell`

```python
openbacktesting.Strategy.sell(self, *, qty: 'float' = <_Unset.VALUE: 'omitted'>, amount: 'float' = <_Unset.VALUE: 'omitted'>, percent: 'float' = <_Unset.VALUE: 'omitted'>, limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order'
```

提交增量订单；qty/amount/percent 三选一，percent=20 表示权益20%。

全部省略时使用默认数量。金额为单币种名义预算，不含费用；
按请求时 Close 换算并冻结，成交时仍可能拒绝。只减仓须显式 qty。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-ta"></a>

### ta

完整对象：`openbacktesting.Strategy.ta`

```python
openbacktesting.Strategy.ta(self) -> 'TechnicalAnalysis'
```

当前运行的指标入口，例如 ta.ema(length=20)、ta.macd().histogram。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-trades"></a>

### trades

完整对象：`openbacktesting.Strategy.trades`

```python
openbacktesting.Strategy.trades(self) -> 'tuple[Trade, ...]'
```

当前仍持有的交易列表，区别于已结算的 closed_trades。

List of active trades (see `Trade`).

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-volume"></a>

### volume

完整对象：`openbacktesting.Strategy.volume`

```python
openbacktesting.Strategy.volume(self) -> 'IndicatorHandle'
```

成交量序列；缺失 Volume 保留 NaN。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-instrument"></a>

### instrument

完整对象：`openbacktesting.Strategy.instrument`

```python
openbacktesting.Strategy.instrument(self) -> 'InstrumentSpec'
```

本次运行的资产规则。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-order-target-value"></a>

### order_target_value

完整对象：`openbacktesting.Strategy.order_target_value`

```python
openbacktesting.Strategy.order_target_value(self, *, target: 'float', limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order | None'
```

以请求时Close把目标净名义换算为数量；显式条件与数量目标一致。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-order-target-quantity"></a>

### order_target_quantity

完整对象：`openbacktesting.Strategy.order_target_quantity`

```python
openbacktesting.Strategy.order_target_quantity(self, *, target: 'float', limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order | None'
```

按实际净仓生成差额订单；条件始终校验，相同活动目标复用。

target 为目标资产数量；无需下单时返回 None。仅支持净额模式。
所有参数必须按名称提供，limit/stop/sl/tp 均为绝对价格。
无差额时仍校验价格、期限和标签，但不虚构买卖方向检查保护关系。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-order-target-percent"></a>

### order_target_percent

完整对象：`openbacktesting.Strategy.order_target_percent`

```python
openbacktesting.Strategy.order_target_percent(self, *, target: 'float', limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order | None'
```

以请求时权益比例确定目标净名义；不持续再平衡或保证成交权重。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-on-finish"></a>

### on_finish

完整对象：`openbacktesting.Strategy.on_finish`

```python
openbacktesting.Strategy.on_finish(self, summary: 'RunSummary')
```

接收冻结结束摘要；异常结束也调用，禁止交易。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-close-position"></a>

### close_position

完整对象：`openbacktesting.Strategy.close_position`

```python
openbacktesting.Strategy.close_position(self, portion: 'float | None' = None) -> 'tuple[Order, ...]'
```

逐批次退出；空仓返回空元组，self.close仍是行情。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-on-start"></a>

### on_start

完整对象：`openbacktesting.Strategy.on_start`

```python
openbacktesting.Strategy.on_start(self)
```

初始化完成后的单次通知；此时不可下单。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-on-fill"></a>

### on_fill

完整对象：`openbacktesting.Strategy.on_fill`

```python
openbacktesting.Strategy.on_fill(self, fill: 'Fill')
```

接收实际成交事实；回调不递归触发撮合。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-account"></a>

### account

完整对象：`openbacktesting.Strategy.account`

```python
openbacktesting.Strategy.account(self) -> 'AccountSnapshot'
```

当前余额、权益、实际费用及保证金的冻结快照。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-submit-oco"></a>

### submit_oco

完整对象：`openbacktesting.Strategy.submit_oco`

```python
openbacktesting.Strategy.submit_oco(self, *, first: 'OrderRequest', second: 'OrderRequest') -> 'OrderGroup'
```

原子提交两个入场请求；先验证两笔，first优先，返回可查询组。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-on-order"></a>

### on_order

完整对象：`openbacktesting.Strategy.on_order`

```python
openbacktesting.Strategy.on_order(self, event: 'OrderEvent')
```

接收冻结订单事件；新请求最早于下一根执行。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-plotting"></a>

### plotting

完整对象：`openbacktesting.Strategy.plotting`

```python
openbacktesting.Strategy.plotting(self) -> 'Plotting'
```

当前运行的纯数据绘图入口；init 声明，运行回调写入。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-timeframe"></a>

### timeframe

完整对象：`openbacktesting.Strategy.timeframe`

```python
openbacktesting.Strategy.timeframe(self) -> 'Timeframe | None'
```

本次图表周期；低层未提供上下文时为 None，不从行情猜测。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-data-index"></a>

### data_index

完整对象：`openbacktesting.Strategy.data_index`

```python
openbacktesting.Strategy.data_index(self) -> 'pd.Index'
```

当前可见索引；保存的 pandas 对象不随游标更新。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-bar-index"></a>

### bar_index

完整对象：`openbacktesting.Strategy.bar_index`

```python
openbacktesting.Strategy.bar_index(self) -> 'int'
```

当前零起点数据位置；init、on_finish 和运行结束后不可读。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-bar-state"></a>

### bar_state

完整对象：`openbacktesting.Strategy.bar_state`

```python
openbacktesting.Strategy.bar_state(self) -> 'BarState'
```

当前数据首尾的冻结快照；提前终止不会将当前位置改称末根。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-log"></a>

### log

完整对象：`openbacktesting.Strategy.log`

```python
openbacktesting.Strategy.log(self) -> 'StrategyLog'
```

当前运行的结构化日志；在作者回调中使用 info、warning 和 error。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-strategy-closed-trade-stats"></a>

### closed_trade_stats

完整对象：`openbacktesting.Strategy.closed_trade_stats`

```python
openbacktesting.Strategy.closed_trade_stats(self) -> 'ClosedTradeStats'
```

读取冻结的已关闭片段统计，包含已分摊费用，不包含浮盈亏。

每次读取不扫描历史；所有生命周期及运行结束后均可读。
same_close 成交前不可提前看到其结果；保存的值不随新成交变化。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-backtest-declaration"></a>

## backtest

完整对象：`openbacktesting.backtest`

```python
openbacktesting.backtest(*, cash: float = 10000, spread: float = 0.0, commission_type: openbacktesting.simulation.config.CommissionType = <CommissionType.PERCENT: 'percent'>, commission_value: float = 0.0, risk_free_rate: float = 0.0, default_qty_type: openbacktesting.simulation.config.QuantityType = <QuantityType.FIXED: 'fixed'>, default_qty_value: float | None = None, margin: float = 1.0, execution_timing: openbacktesting.simulation.config.ExecutionTiming = <ExecutionTiming.NEXT_OPEN: 'next_open'>, slippage_type: openbacktesting.simulation.config.SlippageType = <SlippageType.BPS: 'bps'>, slippage_value: float = 0.0, allow_short: bool = True, max_gross_exposure: float | None = None, hedging: bool = False, exclusive_orders: bool = False, end_policy: openbacktesting.simulation.config.EndPolicy = <EndPolicy.MARK_TO_MARKET: 'mark_to_market'>) -> collections.abc.Callable[[type[~_S]], type[~_S]]
```

将默认回测设置附在具体策略类上；实际行情和运行由宿主提供。

只接受基础值和对应枚举成员；固定选项不接受裸字符串或其他枚举。
仅支持带括号的装饰器形式。算法参数继续使用 inputs，不接受品种、
周期或资源选项；配置模型由框架构造，返回原策略类。

Args:
    cash: 正有限初始账户余额。
    spread: 每次买卖执行的价差小数比例，范围 [0,1)。
    commission_type: 单一佣金类型；PERCENT、CASH_PER_ORDER 或 CASH_PER_CONTRACT。
    commission_value: PERCENT 使用 [-10,10) 百分数，0.2 表示 0.2%，负值为返佣；
        其他类型为非负金额，分别按实际 Fill 或实际资产单位收取。
    risk_free_rate: (-1,1) 年化小数，仅用于统计，不向账户计息。
    default_qty_type: FIXED 为固定数量，PERCENT_OF_EQUITY 为权益百分数。
    default_qty_value: None 禁用默认数量；FIXED 为正数，权益百分数为 (0,100]。
        仅普通 buy/sell 省略 qty 时按请求时 Close 和权益预算、向零取整并冻结。
    margin: (0,1] 保证金小数比例，不放大默认数量预算。
    execution_timing: NEXT_OPEN 或 SAME_CLOSE；后者仅处理 next 新增无条件市价单。
    slippage_type: FIXED 为固定价格距离，BPS 为基点。
    slippage_value: 非负滑点值，零为无滑点。
    allow_short: 是否允许新增空头，严格 bool。
    max_gross_exposure: None 或正的总名义／权益倍数上限。
    hedging: 是否保留双向批次，严格 bool。
    exclusive_orders: 新普通入场是否撤旧入场并提交旧仓退出，严格 bool。
    end_policy: MARK_TO_MARKET 保留持仓估值，CLOSE_AT_LAST_CLOSE 清算实际持仓。

Raises:
    TypeError: 类型、枚举、字段或装饰目标不合法。
    ValueError: 数值越界或同一策略重复声明。

源码：`src/openbacktesting/strategy/declaration.py`。

<a id="openbacktesting-barstate"></a>

## BarState

完整对象：`openbacktesting.BarState`

```python
openbacktesting.BarState(is_first: bool, is_last: bool) -> None
```

当前执行位置的首尾快照；保存后不随运行游标变化。

is_first 表示本次输入第 0 根；is_last 表示本次输入末根，不等同于运行结束。

源码：`src/openbacktesting/strategy/bar_state.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `is_first` | `<class 'bool'>` |
| `is_last` | `<class 'bool'>` |

<a id="openbacktesting-barstate-is-first"></a>

### is_first

完整对象：`openbacktesting.BarState.is_first`

<a id="openbacktesting-barstate-is-last"></a>

### is_last

完整对象：`openbacktesting.BarState.is_last`

<a id="openbacktesting-logs-strategylog"></a>

## StrategyLog

完整对象：`openbacktesting.logs.StrategyLog`

```python
openbacktesting.logs.StrategyLog(collector: openbacktesting.logs._Collector)
```

策略的只读日志句柄，通过 self.log 使用，不需要作者构造。

活动作者回调内可记录字符串；error 仅表示级别，不中止回测。
自动记录实际调用文件与行号，结束后调用抛 RuntimeError。

源码：`src/openbacktesting/logs.py`。

<a id="openbacktesting-logs-strategylog-info"></a>

### info

完整对象：`openbacktesting.logs.StrategyLog.info`

```python
openbacktesting.logs.StrategyLog.info(self, message: str) -> None
```

记录普通信息，保留空字符串、中文和换行。

源码：`src/openbacktesting/logs.py`。

<a id="openbacktesting-logs-strategylog-warning"></a>

### warning

完整对象：`openbacktesting.logs.StrategyLog.warning`

```python
openbacktesting.logs.StrategyLog.warning(self, message: str) -> None
```

记录警告信息，不改变策略执行。

源码：`src/openbacktesting/logs.py`。

<a id="openbacktesting-logs-strategylog-error"></a>

### error

完整对象：`openbacktesting.logs.StrategyLog.error`

```python
openbacktesting.logs.StrategyLog.error(self, message: str) -> None
```

记录错误级别信息；需要中止策略时由作者显式 raise。

源码：`src/openbacktesting/logs.py`。

<a id="openbacktesting-commissiontype"></a>

## CommissionType

完整成员：`CommissionType.PERCENT = "percent"`、`CommissionType.CASH_PER_ORDER = "cash_per_order"`、`CommissionType.CASH_PER_CONTRACT = "cash_per_contract"`。单位和范围见[作者参数表](../guides/author.md#平铺回测设置)。

完整对象：`openbacktesting.CommissionType`

```python
openbacktesting.CommissionType(*values)
```

作者佣金类型；PERCENT 使用百分数，其余成员使用账户金额。

源码：`src/openbacktesting/simulation/config.py`。

<a id="openbacktesting-commissiontype-percent"></a>

### PERCENT

宿主 JSON 值为 `"percent"`。

完整对象：`openbacktesting.CommissionType.PERCENT`

作者佣金类型；PERCENT 使用百分数，其余成员使用账户金额。

<a id="openbacktesting-commissiontype-cash-per-order"></a>

### CASH_PER_ORDER

宿主 JSON 值为 `"cash_per_order"`。

完整对象：`openbacktesting.CommissionType.CASH_PER_ORDER`

作者佣金类型；PERCENT 使用百分数，其余成员使用账户金额。

<a id="openbacktesting-commissiontype-cash-per-contract"></a>

### CASH_PER_CONTRACT

宿主 JSON 值为 `"cash_per_contract"`。

完整对象：`openbacktesting.CommissionType.CASH_PER_CONTRACT`

作者佣金类型；PERCENT 使用百分数，其余成员使用账户金额。

<a id="openbacktesting-quantitytype"></a>

## QuantityType

完整成员：`QuantityType.FIXED = "fixed"`、`QuantityType.PERCENT_OF_EQUITY = "percent_of_equity"`。单位和范围见[作者参数表](../guides/author.md#平铺回测设置)。

完整对象：`openbacktesting.QuantityType`

```python
openbacktesting.QuantityType(*values)
```

默认下单量：固定资产数量，或请求时权益的百分数。

源码：`src/openbacktesting/simulation/config.py`。

<a id="openbacktesting-quantitytype-fixed"></a>

### FIXED

宿主 JSON 值为 `"fixed"`。

完整对象：`openbacktesting.QuantityType.FIXED`

默认下单量：固定资产数量，或请求时权益的百分数。

<a id="openbacktesting-quantitytype-percent-of-equity"></a>

### PERCENT_OF_EQUITY

宿主 JSON 值为 `"percent_of_equity"`。

完整对象：`openbacktesting.QuantityType.PERCENT_OF_EQUITY`

默认下单量：固定资产数量，或请求时权益的百分数。

<a id="openbacktesting-slippagetype"></a>

## SlippageType

完整成员：`SlippageType.FIXED = "fixed"`、`SlippageType.BPS = "bps"`。单位和范围见[作者参数表](../guides/author.md#平铺回测设置)。

完整对象：`openbacktesting.SlippageType`

```python
openbacktesting.SlippageType(*values)
```

滑点距离：固定价格单位，或价格的基点数。

源码：`src/openbacktesting/simulation/config.py`。

<a id="openbacktesting-slippagetype-fixed"></a>

### FIXED

宿主 JSON 值为 `"fixed"`。

完整对象：`openbacktesting.SlippageType.FIXED`

滑点距离：固定价格单位，或价格的基点数。

<a id="openbacktesting-slippagetype-bps"></a>

### BPS

宿主 JSON 值为 `"bps"`。

完整对象：`openbacktesting.SlippageType.BPS`

滑点距离：固定价格单位，或价格的基点数。

<a id="openbacktesting-executiontiming"></a>

## ExecutionTiming

完整成员：`ExecutionTiming.NEXT_OPEN = "next_open"`、`ExecutionTiming.SAME_CLOSE = "same_close"`。单位和范围见[作者参数表](../guides/author.md#平铺回测设置)。

完整对象：`openbacktesting.ExecutionTiming`

```python
openbacktesting.ExecutionTiming(*values)
```

执行时机：最早下一根处理，或本根收盘处理新增无条件市价单。

源码：`src/openbacktesting/simulation/config.py`。

<a id="openbacktesting-executiontiming-next-open"></a>

### NEXT_OPEN

宿主 JSON 值为 `"next_open"`。

完整对象：`openbacktesting.ExecutionTiming.NEXT_OPEN`

执行时机：最早下一根处理，或本根收盘处理新增无条件市价单。

<a id="openbacktesting-executiontiming-same-close"></a>

### SAME_CLOSE

宿主 JSON 值为 `"same_close"`。

完整对象：`openbacktesting.ExecutionTiming.SAME_CLOSE`

执行时机：最早下一根处理，或本根收盘处理新增无条件市价单。

<a id="openbacktesting-endpolicy"></a>

## EndPolicy

完整成员：`EndPolicy.MARK_TO_MARKET = "mark_to_market"`、`EndPolicy.CLOSE_AT_LAST_CLOSE = "close_at_last_close"`。单位和范围见[作者参数表](../guides/author.md#平铺回测设置)。

完整对象：`openbacktesting.EndPolicy`

```python
openbacktesting.EndPolicy(*values)
```

期末政策：保留持仓估值，或按末收盘价清算实际持仓。

源码：`src/openbacktesting/simulation/config.py`。

<a id="openbacktesting-endpolicy-mark-to-market"></a>

### MARK_TO_MARKET

宿主 JSON 值为 `"mark_to_market"`。

完整对象：`openbacktesting.EndPolicy.MARK_TO_MARKET`

期末政策：保留持仓估值，或按末收盘价清算实际持仓。

<a id="openbacktesting-endpolicy-close-at-last-close"></a>

### CLOSE_AT_LAST_CLOSE

宿主 JSON 值为 `"close_at_last_close"`。

完整对象：`openbacktesting.EndPolicy.CLOSE_AT_LAST_CLOSE`

期末政策：保留持仓估值，或按末收盘价清算实际持仓。
