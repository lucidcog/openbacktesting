# 策略组合与辅助工具

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

辅助函数和可组合策略基类用于重采样、信号驱动、移动止损与批量研究。继承基类时按说明调用 super。

[使用指南](../examples.md) · [兼容与内部入口](classification.md)

<a id="openbacktesting-lib-multibacktest"></a>

## MultiBacktest

完整对象：`openbacktesting.lib.MultiBacktest`

```python
openbacktesting.lib.MultiBacktest(df_list, strategy_cls, **kwargs)
```

在多个数据集上运行同一策略，汇总各数据集统计。


Multi-dataset `openbacktesting.engine.Backtest` wrapper.

Run supplied `openbacktesting.engine.Strategy` on several instruments,
in parallel.  Used for comparing strategy runs across many instruments
or classes of instruments. Example:

    from openbacktesting.test import EURUSD, BTCUSD, SmaCross
    btm = MultiBacktest([EURUSD, BTCUSD], SmaCross)
    stats_per_ticker: pd.DataFrame = btm.run(fast=10, slow=20)
    heatmap_per_ticker: pd.DataFrame = btm.optimize(...)

源码：`src/openbacktesting/simulation/variants.py`。

<a id="openbacktesting-lib-multibacktest-optimize"></a>

### optimize

完整对象：`openbacktesting.lib.MultiBacktest.optimize`

```python
openbacktesting.lib.MultiBacktest.optimize(self, **kwargs) -> 'pd.DataFrame'
```

分别优化各数据集的参数，汇总参数评分结果。


Wraps `openbacktesting.engine.Backtest.optimize`, but returns `pd.DataFrame` with
currency indexes in columns.

    heatmap: pd.DataFrame = btm.optimize(...)
    mean_scores = heatmap.mean(axis=1)

源码：`src/openbacktesting/simulation/variants.py`。

<a id="openbacktesting-lib-multibacktest-run"></a>

### run

完整对象：`openbacktesting.lib.MultiBacktest.run`

```python
openbacktesting.lib.MultiBacktest.run(self, **kwargs)
```

在每份数据上执行回测，并按数据集列返回统计表。


Wraps `openbacktesting.engine.Backtest.run`. Returns `pd.DataFrame` with
currency indexes in columns.

源码：`src/openbacktesting/simulation/variants.py`。

<a id="openbacktesting-lib-ohlcv-agg"></a>

## OHLCV_AGG

行情重采样的默认聚合规则：开盘取首值，最高/最低取极值，收盘取末值，成交量求和。

`openbacktesting.lib.OHLCV_AGG` = `OrderedDict({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})`。

<a id="openbacktesting-lib-signalstrategy"></a>

## SignalStrategy

完整对象：`openbacktesting.lib.SignalStrategy`

```python
openbacktesting.lib.SignalStrategy(broker, data, params)
```

按预计算的进入与退出信号运行的可组合策略基类。


A simple helper strategy that operates on position entry/exit signals.
This makes the backtest of the strategy simulate a [vectorized backtest].
用法见使用手册的可运行示例。

[vectorized backtest]: https://altpower.app/?q=vectorized+backtest

To use this helper strategy, subclass it, override its
`openbacktesting.engine.Strategy.init` method,
and set the signal vector by calling
`openbacktesting.lib.SignalStrategy.set_signal` method from within it.

    class ExampleStrategy(SignalStrategy):
        def init(self):
            super().init()
            self.set_signal(sma1 > sma2, sma1 < sma2)

Remember to call `super().init()` and `super().next()` in your
overridden methods.

源码：`src/openbacktesting/strategy/templates.py`。

<a id="openbacktesting-lib-signalstrategy-next"></a>

### next

完整对象：`openbacktesting.lib.SignalStrategy.next`

```python
openbacktesting.lib.SignalStrategy.next(self)
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

源码：`src/openbacktesting/strategy/templates.py`。

<a id="openbacktesting-lib-signalstrategy-set-signal"></a>

### set_signal

完整对象：`openbacktesting.lib.SignalStrategy.set_signal`

```python
openbacktesting.lib.SignalStrategy.set_signal(self, entry_size: 'Sequence[float]', exit_portion: 'Sequence[float] | None' = None)
```

登记真实资产数量及退出比例序列；正数开多、负数开空，零不入场。


Set entry/exit signal vectors (arrays).

A long entry signal is considered present wherever `entry_size`
is greater than zero, and a short signal wherever `entry_size`
is less than zero, following `openbacktesting.engine.Order.size` semantics.

If `exit_portion` is provided, a nonzero value closes portion the position
(see `openbacktesting.engine.Trade.close()`) in the respective direction
(positive values close long trades, negative short).

稀疏信号不影响逐根回调，NaN 不触发交易。

源码：`src/openbacktesting/strategy/templates.py`。

<a id="openbacktesting-lib-signalstrategy-instrument"></a>

### instrument

完整对象：`openbacktesting.lib.SignalStrategy.instrument`

```python
openbacktesting.lib.SignalStrategy.instrument(self) -> 'InstrumentSpec'
```

本次运行的资产规则。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-order-target-value"></a>

### order_target_value

完整对象：`openbacktesting.lib.SignalStrategy.order_target_value`

```python
openbacktesting.lib.SignalStrategy.order_target_value(self, *, target: 'float', limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order | None'
```

以请求时Close把目标净名义换算为数量；显式条件与数量目标一致。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-order-target-quantity"></a>

### order_target_quantity

完整对象：`openbacktesting.lib.SignalStrategy.order_target_quantity`

```python
openbacktesting.lib.SignalStrategy.order_target_quantity(self, *, target: 'float', limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order | None'
```

按实际净仓生成差额订单；条件始终校验，相同活动目标复用。

target 为目标资产数量；无需下单时返回 None。仅支持净额模式。
所有参数必须按名称提供，limit/stop/sl/tp 均为绝对价格。
无差额时仍校验价格、期限和标签，但不虚构买卖方向检查保护关系。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-order-target-percent"></a>

### order_target_percent

完整对象：`openbacktesting.lib.SignalStrategy.order_target_percent`

```python
openbacktesting.lib.SignalStrategy.order_target_percent(self, *, target: 'float', limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order | None'
```

以请求时权益比例确定目标净名义；不持续再平衡或保证成交权重。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-on-finish"></a>

### on_finish

完整对象：`openbacktesting.lib.SignalStrategy.on_finish`

```python
openbacktesting.lib.SignalStrategy.on_finish(self, summary: 'RunSummary')
```

接收冻结结束摘要；异常结束也调用，禁止交易。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-close-position"></a>

### close_position

完整对象：`openbacktesting.lib.SignalStrategy.close_position`

```python
openbacktesting.lib.SignalStrategy.close_position(self, portion: 'float | None' = None) -> 'tuple[Order, ...]'
```

逐批次退出；空仓返回空元组，self.close仍是行情。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-on-start"></a>

### on_start

完整对象：`openbacktesting.lib.SignalStrategy.on_start`

```python
openbacktesting.lib.SignalStrategy.on_start(self)
```

初始化完成后的单次通知；此时不可下单。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-on-fill"></a>

### on_fill

完整对象：`openbacktesting.lib.SignalStrategy.on_fill`

```python
openbacktesting.lib.SignalStrategy.on_fill(self, fill: 'Fill')
```

接收实际成交事实；回调不递归触发撮合。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-account"></a>

### account

完整对象：`openbacktesting.lib.SignalStrategy.account`

```python
openbacktesting.lib.SignalStrategy.account(self) -> 'AccountSnapshot'
```

当前余额、权益、实际费用及保证金的冻结快照。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-submit-oco"></a>

### submit_oco

完整对象：`openbacktesting.lib.SignalStrategy.submit_oco`

```python
openbacktesting.lib.SignalStrategy.submit_oco(self, *, first: 'OrderRequest', second: 'OrderRequest') -> 'OrderGroup'
```

原子提交两个入场请求；先验证两笔，first优先，返回可查询组。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-on-order"></a>

### on_order

完整对象：`openbacktesting.lib.SignalStrategy.on_order`

```python
openbacktesting.lib.SignalStrategy.on_order(self, event: 'OrderEvent')
```

接收冻结订单事件；新请求最早于下一根执行。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-signalstrategy-closed-trade-stats"></a>

### closed_trade_stats

完整对象：`openbacktesting.lib.SignalStrategy.closed_trade_stats`

```python
openbacktesting.lib.SignalStrategy.closed_trade_stats(self) -> 'ClosedTradeStats'
```

读取冻结的已关闭片段统计，包含已分摊费用，不包含浮盈亏。

每次读取不扫描历史；所有生命周期及运行结束后均可读。
same_close 成交前不可提前看到其结果；保存的值不随新成交变化。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trades-agg"></a>

## TRADES_AGG

交易表重采样时各字段使用的聚合规则。

`openbacktesting.lib.TRADES_AGG` = `OrderedDict({'Size': 'sum', 'EntryBar': 'first', 'ExitBar': 'last', 'EntryPrice': 'mean', 'ExitPrice': 'mean', 'PnL': 'sum', 'ReturnPct': 'mean', 'EntryTime': 'first', 'ExitTime': 'last', 'Duration': 'sum'})`。

<a id="openbacktesting-lib-trailingstrategy"></a>

## TrailingStrategy

完整对象：`openbacktesting.lib.TrailingStrategy`

```python
openbacktesting.lib.TrailingStrategy(broker, data, params)
```

依据 ATR 更新交易止损的可组合策略基类。


A strategy with automatic trailing stop-loss, trailing the current
price at distance of some multiple of average true range (ATR). Call
`TrailingStrategy.set_trailing_sl()` to set said multiple
(`6` by default).
用法见使用手册的可运行示例。


Remember to call `super().init()` and `super().next()` in your
overridden methods.

源码：`src/openbacktesting/strategy/templates.py`。

<a id="openbacktesting-lib-trailingstrategy-init"></a>

### init

完整对象：`openbacktesting.lib.TrailingStrategy.init`

```python
openbacktesting.lib.TrailingStrategy.init(self)
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

源码：`src/openbacktesting/strategy/templates.py`。

<a id="openbacktesting-lib-trailingstrategy-next"></a>

### next

完整对象：`openbacktesting.lib.TrailingStrategy.next`

```python
openbacktesting.lib.TrailingStrategy.next(self)
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

源码：`src/openbacktesting/strategy/templates.py`。

<a id="openbacktesting-lib-trailingstrategy-set-atr-periods"></a>

### set_atr_periods

完整对象：`openbacktesting.lib.TrailingStrategy.set_atr_periods`

```python
openbacktesting.lib.TrailingStrategy.set_atr_periods(self, periods: 'int' = 100)
```

设置因果 ATR 窗口；默认100，预热期不回填、不设置 ATR 止损。

源码：`src/openbacktesting/strategy/templates.py`。

<a id="openbacktesting-lib-trailingstrategy-set-trailing-pct"></a>

### set_trailing_pct

完整对象：`openbacktesting.lib.TrailingStrategy.set_trailing_pct`

```python
openbacktesting.lib.TrailingStrategy.set_trailing_pct(self, pct: 'float' = 0.05)
```

按当前已确认价格计算百分比距离，默认5%，不使用全样本估计。

pct必须在0与1之间。多头止损仅上移、空头仅下移；更新最早下一根生效。
next逐根调用；ATR未就绪时跳过止损更新，百分比模式不依赖ATR。

源码：`src/openbacktesting/strategy/templates.py`。

<a id="openbacktesting-lib-trailingstrategy-set-trailing-sl"></a>

### set_trailing_sl

完整对象：`openbacktesting.lib.TrailingStrategy.set_trailing_sl`

```python
openbacktesting.lib.TrailingStrategy.set_trailing_sl(self, n_atr: 'float' = 6)
```

设置后续跟踪止损使用的 ATR 倍数。


Set the future trailing stop-loss as some multiple (`n_atr`)
average true bar ranges away from the current price.

源码：`src/openbacktesting/strategy/templates.py`。

<a id="openbacktesting-lib-trailingstrategy-instrument"></a>

### instrument

完整对象：`openbacktesting.lib.TrailingStrategy.instrument`

```python
openbacktesting.lib.TrailingStrategy.instrument(self) -> 'InstrumentSpec'
```

本次运行的资产规则。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-order-target-value"></a>

### order_target_value

完整对象：`openbacktesting.lib.TrailingStrategy.order_target_value`

```python
openbacktesting.lib.TrailingStrategy.order_target_value(self, *, target: 'float', limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order | None'
```

以请求时Close把目标净名义换算为数量；显式条件与数量目标一致。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-order-target-quantity"></a>

### order_target_quantity

完整对象：`openbacktesting.lib.TrailingStrategy.order_target_quantity`

```python
openbacktesting.lib.TrailingStrategy.order_target_quantity(self, *, target: 'float', limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order | None'
```

按实际净仓生成差额订单；条件始终校验，相同活动目标复用。

target 为目标资产数量；无需下单时返回 None。仅支持净额模式。
所有参数必须按名称提供，limit/stop/sl/tp 均为绝对价格。
无差额时仍校验价格、期限和标签，但不虚构买卖方向检查保护关系。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-order-target-percent"></a>

### order_target_percent

完整对象：`openbacktesting.lib.TrailingStrategy.order_target_percent`

```python
openbacktesting.lib.TrailingStrategy.order_target_percent(self, *, target: 'float', limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, reduce_only: 'bool' = False, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'Order | None'
```

以请求时权益比例确定目标净名义；不持续再平衡或保证成交权重。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-on-finish"></a>

### on_finish

完整对象：`openbacktesting.lib.TrailingStrategy.on_finish`

```python
openbacktesting.lib.TrailingStrategy.on_finish(self, summary: 'RunSummary')
```

接收冻结结束摘要；异常结束也调用，禁止交易。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-close-position"></a>

### close_position

完整对象：`openbacktesting.lib.TrailingStrategy.close_position`

```python
openbacktesting.lib.TrailingStrategy.close_position(self, portion: 'float | None' = None) -> 'tuple[Order, ...]'
```

逐批次退出；空仓返回空元组，self.close仍是行情。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-on-start"></a>

### on_start

完整对象：`openbacktesting.lib.TrailingStrategy.on_start`

```python
openbacktesting.lib.TrailingStrategy.on_start(self)
```

初始化完成后的单次通知；此时不可下单。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-on-fill"></a>

### on_fill

完整对象：`openbacktesting.lib.TrailingStrategy.on_fill`

```python
openbacktesting.lib.TrailingStrategy.on_fill(self, fill: 'Fill')
```

接收实际成交事实；回调不递归触发撮合。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-account"></a>

### account

完整对象：`openbacktesting.lib.TrailingStrategy.account`

```python
openbacktesting.lib.TrailingStrategy.account(self) -> 'AccountSnapshot'
```

当前余额、权益、实际费用及保证金的冻结快照。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-submit-oco"></a>

### submit_oco

完整对象：`openbacktesting.lib.TrailingStrategy.submit_oco`

```python
openbacktesting.lib.TrailingStrategy.submit_oco(self, *, first: 'OrderRequest', second: 'OrderRequest') -> 'OrderGroup'
```

原子提交两个入场请求；先验证两笔，first优先，返回可查询组。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-on-order"></a>

### on_order

完整对象：`openbacktesting.lib.TrailingStrategy.on_order`

```python
openbacktesting.lib.TrailingStrategy.on_order(self, event: 'OrderEvent')
```

接收冻结订单事件；新请求最早于下一根执行。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-trailingstrategy-closed-trade-stats"></a>

### closed_trade_stats

完整对象：`openbacktesting.lib.TrailingStrategy.closed_trade_stats`

```python
openbacktesting.lib.TrailingStrategy.closed_trade_stats(self) -> 'ClosedTradeStats'
```

读取冻结的已关闭片段统计，包含已分摊费用，不包含浮盈亏。

每次读取不扫描历史；所有生命周期及运行结束后均可读。
same_close 成交前不可提前看到其结果；保存的值不随新成交变化。

源码：`src/openbacktesting/strategy/base.py`。

<a id="openbacktesting-lib-barssince"></a>

## barssince

完整对象：`openbacktesting.lib.barssince`

```python
openbacktesting.lib.barssince(condition: 'Sequence[bool]', default=inf) -> 'int'
```

查询条件序列最近一次成立距当前的间隔；这是标量辅助函数。


Return the number of bars since `condition` sequence was last `True`,
or if never, return `default`.

    >>> barssince(self.data.Close > self.data.Open)
    3

源码：`src/openbacktesting/strategy/helpers.py`。

<a id="openbacktesting-lib-compute-stats"></a>

## compute_stats

完整对象：`openbacktesting.lib.compute_stats`

```python
openbacktesting.lib.compute_stats(*, stats: 'pd.Series', data: 'pd.DataFrame', trades: 'pd.DataFrame' = None, risk_free_rate: 'float' = Ellipsis) -> 'pd.Series'
```

从既有结果、数据及可选交易子集重新计算绩效统计。


(Re-)compute strategy performance metrics.

`stats` is the statistics series as returned by `openbacktesting.engine.Backtest.run()`.
`data` is OHLC data as passed to the `openbacktesting.engine.Backtest`
the `stats` were obtained in.
`trades` can be a dataframe subset of `stats._trades` (e.g. only long trades).
risk_free_rate 为年化小数，用于 Sharpe、Sortino 与 Alpha；省略时继承最近统计值，
缺失记录回退零，显式零覆盖，None 无效。重算不改写原运行快照或实际费用。
初始资金继承 statistics_initial_equity；历史缺失记录回退首条权益。
初始资金必须为正数有限值，交易子集的近似权益也从该本金开始。

    >>> stats = Backtest(GOOG, MyStrategy).run()
    >>> only_long_trades = stats._trades[stats._trades.Size > 0]
    >>> long_stats = compute_stats(stats=stats, trades=only_long_trades,
    ...                            data=GOOG, risk_free_rate=.02)

源码：`src/openbacktesting/portfolio/helpers.py`。

<a id="openbacktesting-lib-quantile"></a>

## quantile

完整对象：`openbacktesting.lib.quantile`

```python
openbacktesting.lib.quantile(series: 'Sequence', quantile: 'None | float' = None)
```

查询末值的相对排名，或读取指定分位值，取决于 quantile 参数。


If `quantile` is `None`, return the quantile _rank_ of the last
value of `series` wrt former series values.

If `quantile` is a value between 0 and 1, return the _value_ of
`series` at this quantile. If used to working with percentiles, just
divide your percentile amount with 100 to obtain quantiles.

    >>> quantile(self.data.Close[-20:], .1)
    162.130
    >>> quantile(self.data.Close)
    0.13

源码：`src/openbacktesting/strategy/helpers.py`。

<a id="openbacktesting-lib-random-ohlc-data"></a>

## random_ohlc_data

完整对象：`openbacktesting.lib.random_ohlc_data`

```python
openbacktesting.lib.random_ohlc_data(example_data: 'pd.DataFrame', *, frac=1.0, random_state: 'int | None' = None) -> 'Generator[pd.DataFrame, None, None]'
```

迭代生成保留基本行情结构的随机样例，不代表真实市场预测。


OHLC data generator. The generated OHLC data has basic
[descriptive statistics](https://en.wikipedia.org/wiki/Descriptive_statistics)
similar to the provided `example_data`.

`frac` is a fraction of data to sample (with replacement). Values greater
than 1 result in oversampling.

Such random data can be effectively used for stress testing trading
strategy robustness, Monte Carlo simulations, significance testing, etc.

>>> from openbacktesting.test import EURUSD
>>> ohlc_generator = random_ohlc_data(EURUSD)
>>> next(ohlc_generator)  # returns new random data
...
>>> next(ohlc_generator)  # returns new random data
...

源码：`src/openbacktesting/data/generators.py`。

<a id="openbacktesting-lib-resample-apply"></a>

## resample_apply

完整对象：`openbacktesting.lib.resample_apply`

```python
openbacktesting.lib.resample_apply(rule: 'str', func: 'Callable[..., Sequence] | None', series: 'pd.Series | pd.DataFrame | _Array', *args, agg: 'str | dict | None' = None, **kwargs)
```

先重采样并应用函数，再对齐到原日历；策略初始化内自动登记结果句柄。


Apply `func` (such as an indicator) to `series`, resampled to
a time frame specified by `rule`. When called from inside
`openbacktesting.engine.Strategy.init`,
the result (returned) series will be automatically wrapped in
`openbacktesting.engine.Strategy.ind`
wrapper method.

`rule` is a valid [Pandas offset string] indicating
a time frame to resample `series` to.

[Pandas offset string]: http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

`func` is the indicator function to apply on the resampled series.

`series` is a data series (or array), such as any of the
`openbacktesting.engine.Strategy.data` series. Due to pandas
resampling limitations, this only works when input series
has a datetime index.

`agg` is the aggregation function to use on resampled groups of data.
Valid values are anything accepted by `pandas/resample/.agg()`.
Default value for dataframe input is `OHLCV_AGG` dictionary.
Default value for series input is the appropriate entry from `OHLCV_AGG`
if series has a matching name, or otherwise the value `"last"`,
which is suitable for closing prices,
but you might prefer another (e.g. `"max"` for peaks, or similar).

Finally, any `*args` and `**kwargs` that are not already eaten by
implicit `openbacktesting.engine.Strategy.ind` call
are passed to `func`.

For example, if we have a typical moving average function
`SMA(values, lookback_period)`, _hourly_ data source, and need to
apply the moving average MA(10) on a _daily_ time frame, we can do::

    class System(Strategy):
        def init(self):
            self.sma = resample_apply(
                'D', SMA, self.data.Close, 10)

The above short snippet is roughly equivalent to::

    class System(Strategy):
        def init(self):
            # Strategy exposes `self.data` as raw NumPy arrays.
            # Let's convert closing prices back to pandas Series.
            close = self.data.Close.s

            # Resample to daily resolution. Aggregate groups
            # using their last value (i.e. closing price at the end
            # of the day). Notice `label='right'`. If it were set to
            # 'left' (default), the strategy would exhibit
            # look-ahead bias.
            daily = close.resample('D', label='right').agg('last')

            # We apply SMA(10) to daily close prices,
            # then reindex it back to original hourly index,
            # forward-filling the missing values in each day.
            # We make a separate function that returns the final
            # indicator array.
            def SMA(series, n):
                from openbacktesting.test import SMA
                return SMA(series, n).reindex(close.index).ffill()

            # The result equivalent to the short example above:
            self.sma = self.ind(SMA, daily, 10)

源码：`src/openbacktesting/strategy/helpers.py`。
