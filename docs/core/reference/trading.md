# 订单、仓位与交易

<!-- 由 scripts/core_docs.py 生成；请修改事实源后重新生成。 -->

Order 表示待处理订单，Trade 表示单笔交易，Position 汇总当前仓位。平仓请求与成交发生在不同阶段。

[使用指南](../guides/trading.md) · [兼容与内部入口](classification.md)

<a id="openbacktesting-engine-order"></a>

## Order

完整对象：`openbacktesting.engine.Order`

```python
openbacktesting.engine.Order(broker, request, *, group_id=None, kind='entry', eligible=None, sizing=None)
```

稳定订单句柄；request和snapshot为不可变值，cancel可重复调用。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-cancel"></a>

### cancel

完整对象：`openbacktesting.engine.Order.cancel`

```python
openbacktesting.engine.Order.cancel(self)
```

取消未完成订单，终态调用幂等。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-is-contingent"></a>

### is_contingent

完整对象：`openbacktesting.engine.Order.is_contingent`

```python
openbacktesting.engine.Order.is_contingent(self)
```

是否批次保护退出。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-is-long"></a>

### is_long

完整对象：`openbacktesting.engine.Order.is_long`

```python
openbacktesting.engine.Order.is_long(self)
```

是否买向请求。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-is-short"></a>

### is_short

完整对象：`openbacktesting.engine.Order.is_short`

```python
openbacktesting.engine.Order.is_short(self)
```

是否卖向请求。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-limit"></a>

### limit

完整对象：`openbacktesting.engine.Order.limit`

```python
openbacktesting.engine.Order.limit(self)
```

不可变请求限价。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-parent-trade"></a>

### parent_trade

完整对象：`openbacktesting.engine.Order.parent_trade`

```python
openbacktesting.engine.Order.parent_trade(self)
```

关联的活跃批次；关闭后返回None。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-size"></a>

### size

完整对象：`openbacktesting.engine.Order.size`

```python
openbacktesting.engine.Order.size(self)
```

原始有符号资产数量。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-sl"></a>

### sl

完整对象：`openbacktesting.engine.Order.sl`

```python
openbacktesting.engine.Order.sl(self)
```

请求的初始止损价。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-stop"></a>

### stop

完整对象：`openbacktesting.engine.Order.stop`

```python
openbacktesting.engine.Order.stop(self)
```

当前有效触发价；原始条件保留于request。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-tag"></a>

### tag

完整对象：`openbacktesting.engine.Order.tag`

```python
openbacktesting.engine.Order.tag(self)
```

用户标签的独立纯值副本。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-tp"></a>

### tp

完整对象：`openbacktesting.engine.Order.tp`

```python
openbacktesting.engine.Order.tp(self)
```

请求的初始止盈价。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-status"></a>

### status

完整对象：`openbacktesting.engine.Order.status`

```python
openbacktesting.engine.Order.status(self)
```

当前状态；历史状态从事件查询。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-request"></a>

### request

返回冻结的 NormalizedOrderRequest：可读取 side、qty、limit、stop、sl、tp、reduce_only、trade_id、expires_at、valid_bars、tag_json 和 tag。tag 返回独立 JSON 副本。此对象是已登记订单的观察值；作者使用 OrderRequest 描述待提交入场。

完整对象：`openbacktesting.engine.Order.request`

```python
openbacktesting.engine.Order.request(self) -> 'NormalizedOrderRequest'
```

不可替换的原始规范化请求。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-snapshot"></a>

### snapshot

完整对象：`openbacktesting.engine.Order.snapshot`

```python
openbacktesting.engine.Order.snapshot(self) -> 'OrderSnapshot'
```

最近一次冻结状态，不暴露可写状态。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-group"></a>

### group

完整对象：`openbacktesting.engine.Order.group`

```python
openbacktesting.engine.Order.group(self)
```

关联OCO或保护组；普通独立订单返回None。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-order-id"></a>

### order_id

完整对象：`openbacktesting.engine.Order.order_id`

```python
openbacktesting.engine.Order.order_id(self)
```

每运行稳定且只读的订单身份。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-order-sizing"></a>

### sizing

完整对象：`openbacktesting.engine.Order.sizing`

```python
openbacktesting.engine.Order.sizing(self) -> 'OrderSizingSnapshot | None'
```

提交时的冻结规模依据；目标、批次退出和内部保护订单为 None。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-position"></a>

## Position

完整对象：`openbacktesting.engine.Position`

```python
openbacktesting.engine.Position(broker)
```

活跃批次汇总；布尔值按总暴露判断。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-position-close"></a>

### close

完整对象：`openbacktesting.engine.Position.close`

```python
openbacktesting.engine.Position.close(self, portion=None)
```

逐批次提交只减仓订单并返回有序元组。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-position-is-long"></a>

### is_long

完整对象：`openbacktesting.engine.Position.is_long`

```python
openbacktesting.engine.Position.is_long(self)
```

是否净多。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-position-is-short"></a>

### is_short

完整对象：`openbacktesting.engine.Position.is_short`

```python
openbacktesting.engine.Position.is_short(self)
```

是否净空。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-position-pl"></a>

### pl

完整对象：`openbacktesting.engine.Position.pl`

```python
openbacktesting.engine.Position.pl(self)
```

包含剩余入场费用的未实现净损益。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-position-size"></a>

### size

完整对象：`openbacktesting.engine.Position.size`

```python
openbacktesting.engine.Position.size(self)
```

有符号净数量。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-position-has-exposure"></a>

### has_exposure

完整对象：`openbacktesting.engine.Position.has_exposure`

```python
openbacktesting.engine.Position.has_exposure(self)
```

是否仍持有任意批次。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-position-snapshot"></a>

### snapshot

完整对象：`openbacktesting.engine.Position.snapshot`

```python
openbacktesting.engine.Position.snapshot(self) -> 'PositionSnapshot'
```

冻结的净仓、总暴露与费用快照。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-position-return-fraction"></a>

### return_fraction

完整对象：`openbacktesting.engine.Position.return_fraction`

```python
openbacktesting.engine.Position.return_fraction(self)
```

净回报小数；双向或空仓无统一成本时为None。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade"></a>

## Trade

完整对象：`openbacktesting.engine.Trade`

```python
openbacktesting.engine.Trade(broker, size, entry_price, entry_bar, tag=None, *, trade_id=None, entry_fill_id='', entry_fee=0, group_id=None)
```

可单独退出及保护的开仓批次；部分退出保留trade_id。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-close"></a>

### close

完整对象：`openbacktesting.engine.Trade.close`

```python
openbacktesting.engine.Trade.close(self, portion=None, *, qty=None)
```

只减仓退出；qty与portion互斥，默认关闭全部。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-entry-time"></a>

### entry_time

完整对象：`openbacktesting.engine.Trade.entry_time`

```python
openbacktesting.engine.Trade.entry_time(self)
```

入场bar索引。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-exit-time"></a>

### exit_time

完整对象：`openbacktesting.engine.Trade.exit_time`

```python
openbacktesting.engine.Trade.exit_time(self)
```

关闭bar索引；活跃时为None。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-is-long"></a>

### is_long

完整对象：`openbacktesting.engine.Trade.is_long`

```python
openbacktesting.engine.Trade.is_long(self)
```

是否多头批次。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-is-short"></a>

### is_short

完整对象：`openbacktesting.engine.Trade.is_short`

```python
openbacktesting.engine.Trade.is_short(self)
```

是否空头批次。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-pl"></a>

### pl

完整对象：`openbacktesting.engine.Trade.pl`

```python
openbacktesting.engine.Trade.pl(self)
```

含分摊费用的净损益；活跃批次包括剩余入场费。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-size"></a>

### size

完整对象：`openbacktesting.engine.Trade.size`

```python
openbacktesting.engine.Trade.size(self)
```

剩余或关闭片段的有符号数量。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-sl"></a>

### sl

完整对象：`openbacktesting.engine.Trade.sl`

```python
openbacktesting.engine.Trade.sl(self)
```

当前止损价；写入会留下撤旧建新的事件。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-tag"></a>

### tag

完整对象：`openbacktesting.engine.Trade.tag`

```python
openbacktesting.engine.Trade.tag(self)
```

入场标签副本。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-tp"></a>

### tp

完整对象：`openbacktesting.engine.Trade.tp`

```python
openbacktesting.engine.Trade.tp(self)
```

当前止盈价；None撤销保护。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-value"></a>

### value

完整对象：`openbacktesting.engine.Trade.value`

```python
openbacktesting.engine.Trade.value(self)
```

按当前或退出价计算的绝对名义价值。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-set-trailing-stop"></a>

### set_trailing_stop

完整对象：`openbacktesting.engine.Trade.set_trailing_stop`

```python
openbacktesting.engine.Trade.set_trailing_stop(self, *, amount=None, percent=None)
```

建立原生跟踪止损，替换固定SL，下一合法bar生效。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-pl-gross"></a>

### pl_gross

完整对象：`openbacktesting.engine.Trade.pl_gross`

```python
openbacktesting.engine.Trade.pl_gross(self)
```

价格毛损益。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-return-fraction"></a>

### return_fraction

完整对象：`openbacktesting.engine.Trade.return_fraction`

```python
openbacktesting.engine.Trade.return_fraction(self)
```

以剩余/分配入场名义为分母的净回报小数。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-engine-trade-group"></a>

### group

完整对象：`openbacktesting.engine.Trade.group`

```python
openbacktesting.engine.Trade.group(self)
```

批次保护组，包含历史替换成员。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-broker-positionsnapshot"></a>

## PositionSnapshot

完整对象：`openbacktesting.broker.PositionSnapshot`

```python
openbacktesting.broker.PositionSnapshot(net_qty: 'float', gross_qty: 'float', long_qty: 'float', short_qty: 'float', long_avg_price: 'float | None', short_avg_price: 'float | None', avg_price: 'float | None', gross_notional: 'float', net_notional: 'float', unrealized_pnl_gross: 'float', unrealized_pnl_net: 'float', entry_fees_remaining: 'float', return_fraction: 'float | None') -> None
```

净仓、双向总暴露与明确毛净损益。

源码：`src/openbacktesting/broker/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `net_qty` | `float` |
| `gross_qty` | `float` |
| `long_qty` | `float` |
| `short_qty` | `float` |
| `long_avg_price` | `float \| None` |
| `short_avg_price` | `float \| None` |
| `avg_price` | `float \| None` |
| `gross_notional` | `float` |
| `net_notional` | `float` |
| `unrealized_pnl_gross` | `float` |
| `unrealized_pnl_net` | `float` |
| `entry_fees_remaining` | `float` |
| `return_fraction` | `float \| None` |

<a id="openbacktesting-broker-positionsnapshot-has-exposure"></a>

### has_exposure

完整对象：`openbacktesting.broker.PositionSnapshot.has_exposure`

```python
openbacktesting.broker.PositionSnapshot.has_exposure(self) -> 'bool'
```

双向净零仓仍有总暴露。

源码：`src/openbacktesting/broker/models.py`。

<a id="openbacktesting-broker-accountsnapshot"></a>

## AccountSnapshot

完整对象：`openbacktesting.broker.AccountSnapshot`

```python
openbacktesting.broker.AccountSnapshot(balance: 'float', equity: 'float', realized_pnl_gross: 'float', unrealized_pnl_gross: 'float', fees_paid: 'float', margin_used: 'float', margin_available: 'float', gross_notional: 'float', net_notional: 'float') -> None
```

单币种线性保证金账户，balance并非证券交收现金。

源码：`src/openbacktesting/broker/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `balance` | `float` |
| `equity` | `float` |
| `realized_pnl_gross` | `float` |
| `unrealized_pnl_gross` | `float` |
| `fees_paid` | `float` |
| `margin_used` | `float` |
| `margin_available` | `float` |
| `gross_notional` | `float` |
| `net_notional` | `float` |

<a id="openbacktesting-broker-orderstatus"></a>

## OrderStatus

完整对象：`openbacktesting.broker.OrderStatus`

```python
openbacktesting.broker.OrderStatus(*values)
```

订单可观察状态；终态不可重新打开。

源码：`src/openbacktesting/broker/models.py`。

<a id="openbacktesting-broker-trade"></a>

## Trade

完整对象：`openbacktesting.broker.Trade`

```python
openbacktesting.broker.Trade(broker, size, entry_price, entry_bar, tag=None, *, trade_id=None, entry_fill_id='', entry_fee=0, group_id=None)
```

可单独退出及保护的开仓批次；部分退出保留trade_id。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-broker-ordergroup"></a>

## OrderGroup

完整对象：`openbacktesting.broker.OrderGroup`

```python
openbacktesting.broker.OrderGroup(broker, group_id, kind)
```

可查询的OCO或批次保护组；取消不等于平仓。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-broker-ordergroup-cancel"></a>

### cancel

完整对象：`openbacktesting.broker.OrderGroup.cancel`

```python
openbacktesting.broker.OrderGroup.cancel(self)
```

取消所有仍活动成员，不自动退出持仓。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-broker-ordergroup-orders"></a>

### orders

完整对象：`openbacktesting.broker.OrderGroup.orders`

```python
openbacktesting.broker.OrderGroup.orders(self)
```

本组全部订单，包含历史终态。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-broker-orderrequest"></a>

## OrderRequest

完整对象：`openbacktesting.broker.OrderRequest`

```python
openbacktesting.broker.OrderRequest(*, side: "Literal['buy', 'sell']", qty: 'float' = <_Unset.VALUE: 'omitted'>, amount: 'float' = <_Unset.VALUE: 'omitted'>, percent: 'float' = <_Unset.VALUE: 'omitted'>, limit: 'float | None' = None, stop: 'float | None' = None, sl: 'float | None' = None, tp: 'float | None' = None, tag: '_JsonValue' = None, expires_at: '_Expiry | None' = None, valid_bars: 'int | None' = None) -> 'None'
```

待提交的冻结入场请求；构造不会登记订单，可在初始化阶段准备。

所有参数必须按名称提供。品种精度、行情时区和保护方向在提交时校验。
``tag`` 支持 JSON 纯值；构造时固化，读取返回独立副本。

Args:
    side: 买入 buy 或卖出 sell。
    qty: 有限正资产数量，与 amount/percent 三选一，不使用默认预算。
    amount: 有限正名义金额，在提交时按 Close 换算，不预留费用。
    percent: (0,100] 的权益百分数，20 表示 20%，在提交时计算。
    limit: 入场限价，None 表示没有限价条件。
    stop: 入场触发价，与入场后的 sl 不同。
    sl: 入场后的绝对止损价。
    tp: 入场后的绝对止盈价。
    tag: 可选用户标签，不参与撮合条件。
    expires_at: 带时区的绝对到期时间，与 valid_bars 互斥。
    valid_bars: 提交后允许执行的 bar 数，必须为正整数。

Raises:
    TypeError: 参数类型、命名或标签类型不合法。
    ValueError: 数量、价格、方向或期限值不合法。

源码：`src/openbacktesting/broker/requests.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `side` | `Literal['buy', 'sell']` |
| `limit` | `float \| None` |
| `stop` | `float \| None` |
| `sl` | `float \| None` |
| `tp` | `float \| None` |
| `expires_at` | `pd.Timestamp \| None` |
| `valid_bars` | `int \| None` |

<a id="openbacktesting-broker-orderrequest-sl"></a>

### sl

完整对象：`openbacktesting.broker.OrderRequest.sl`

<a id="openbacktesting-broker-orderrequest-tag"></a>

### tag

完整对象：`openbacktesting.broker.OrderRequest.tag`

```python
openbacktesting.broker.OrderRequest.tag(self) -> '_JsonValue'
```

独立的 JSON 标签副本；修改副本不改变请求。

源码：`src/openbacktesting/broker/requests.py`。

<a id="openbacktesting-broker-orderrequest-limit"></a>

### limit

完整对象：`openbacktesting.broker.OrderRequest.limit`

<a id="openbacktesting-broker-orderrequest-valid-bars"></a>

### valid_bars

完整对象：`openbacktesting.broker.OrderRequest.valid_bars`

<a id="openbacktesting-broker-orderrequest-tp"></a>

### tp

完整对象：`openbacktesting.broker.OrderRequest.tp`

<a id="openbacktesting-broker-orderrequest-stop"></a>

### stop

完整对象：`openbacktesting.broker.OrderRequest.stop`

<a id="openbacktesting-broker-orderrequest-expires-at"></a>

### expires_at

完整对象：`openbacktesting.broker.OrderRequest.expires_at`

<a id="openbacktesting-broker-orderrequest-qty"></a>

### qty

完整对象：`openbacktesting.broker.OrderRequest.qty`

```python
openbacktesting.broker.OrderRequest.qty(self) -> 'float | None'
```

显式资产数量；其他模式返回 None。

源码：`src/openbacktesting/broker/requests.py`。

<a id="openbacktesting-broker-orderrequest-amount"></a>

### amount

完整对象：`openbacktesting.broker.OrderRequest.amount`

```python
openbacktesting.broker.OrderRequest.amount(self) -> 'float | None'
```

显式名义金额；提交时换算，其他模式返回 None。

源码：`src/openbacktesting/broker/requests.py`。

<a id="openbacktesting-broker-orderrequest-percent"></a>

### percent

完整对象：`openbacktesting.broker.OrderRequest.percent`

```python
openbacktesting.broker.OrderRequest.percent(self) -> 'float | None'
```

显式权益百分数（20 为20%）；其他模式返回 None。

源码：`src/openbacktesting/broker/requests.py`。

<a id="openbacktesting-broker-position"></a>

## Position

完整对象：`openbacktesting.broker.Position`

```python
openbacktesting.broker.Position(broker)
```

活跃批次汇总；布尔值按总暴露判断。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-broker-runsummary"></a>

## RunSummary

完整对象：`openbacktesting.broker.RunSummary`

```python
openbacktesting.broker.RunSummary(reason: 'str', account: 'AccountSnapshot', error: 'str | None' = None) -> None
```

结束钩子的冻结摘要；错误信息不替代原异常。

源码：`src/openbacktesting/broker/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `reason` | `str` |
| `account` | `AccountSnapshot` |
| `error` | `str \| None` |

<a id="openbacktesting-broker-runsummary-error"></a>

### error

完整对象：`openbacktesting.broker.RunSummary.error`

<a id="openbacktesting-broker-tradeallocation"></a>

## TradeAllocation

完整对象：`openbacktesting.broker.TradeAllocation`

```python
openbacktesting.broker.TradeAllocation(allocation_id: 'str', fill_id: 'str', trade_id: 'str', entry_fill_id: 'str', kind: 'str', qty: 'float', fee: 'float', entry_fee: 'float', realized_pnl_gross: 'float') -> None
```

执行量在开仓批次或关闭片段上的分配。

源码：`src/openbacktesting/broker/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `allocation_id` | `str` |
| `fill_id` | `str` |
| `trade_id` | `str` |
| `entry_fill_id` | `str` |
| `kind` | `str` |
| `qty` | `float` |
| `fee` | `float` |
| `entry_fee` | `float` |
| `realized_pnl_gross` | `float` |

<a id="openbacktesting-broker-slippage"></a>

## Slippage

完整对象：`openbacktesting.broker.Slippage`

```python
openbacktesting.broker.Slippage(mode: str = 'none', value: float = 0) -> None
```

无滑点、固定金额或基点滑点；每次成交只应用一次。

源码：`src/openbacktesting/broker/execution.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `mode` | `<class 'str'>` |
| `value` | `<class 'float'>` |

<a id="openbacktesting-broker-slippage-cost"></a>

### cost

完整对象：`openbacktesting.broker.Slippage.cost`

```python
openbacktesting.broker.Slippage.cost(self, price: float) -> float
```

返回非负单单位滑点距离。

源码：`src/openbacktesting/broker/execution.py`。

<a id="openbacktesting-broker-slippage-mode"></a>

### mode

完整对象：`openbacktesting.broker.Slippage.mode`

str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

<a id="openbacktesting-broker-slippage-value"></a>

### value

完整对象：`openbacktesting.broker.Slippage.value`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-broker-ordersnapshot"></a>

## OrderSnapshot

完整对象：`openbacktesting.broker.OrderSnapshot`

```python
openbacktesting.broker.OrderSnapshot(order_id: 'str', status: 'OrderStatus', filled_qty: 'float', remaining_qty: 'float', avg_fill_price: 'float | None', reason: 'str | None', triggered: 'bool') -> None
```

订单在某次状态迁移时的冻结值。

源码：`src/openbacktesting/broker/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `order_id` | `str` |
| `status` | `OrderStatus` |
| `filled_qty` | `float` |
| `remaining_qty` | `float` |
| `avg_fill_price` | `float \| None` |
| `reason` | `str \| None` |
| `triggered` | `bool` |

<a id="openbacktesting-broker-fill"></a>

## Fill

完整对象：`openbacktesting.broker.Fill`

```python
openbacktesting.broker.Fill(fill_id: 'str', order_id: 'str', sequence: 'int', side: 'str', qty: 'float', price: 'float', fee: 'float', bar_index: 'int', timestamp: 'object', phase: 'str', reason: 'str') -> None
```

一次实际执行，费用只在此处记账一次。

源码：`src/openbacktesting/broker/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `fill_id` | `str` |
| `order_id` | `str` |
| `sequence` | `int` |
| `side` | `str` |
| `qty` | `float` |
| `price` | `float` |
| `fee` | `float` |
| `bar_index` | `int` |
| `timestamp` | `object` |
| `phase` | `str` |
| `reason` | `str` |

<a id="openbacktesting-broker-instrumentspec"></a>

## InstrumentSpec

完整对象：`openbacktesting.broker.InstrumentSpec`

```python
openbacktesting.broker.InstrumentSpec(symbol: str = 'asset', quantity_step: float = 1, min_quantity: float | None = None, price_tick: float | None = None, min_notional: float = 0, currency: str | None = None) -> None
```

真实资产数量与价格网格；currency仅作标签。

源码：`src/openbacktesting/broker/instrument.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `symbol` | `<class 'str'>` |
| `quantity_step` | `<class 'float'>` |
| `min_quantity` | `float \| None` |
| `price_tick` | `float \| None` |
| `min_notional` | `<class 'float'>` |
| `currency` | `str \| None` |

<a id="openbacktesting-broker-instrumentspec-symbol"></a>

### symbol

完整对象：`openbacktesting.broker.InstrumentSpec.symbol`

str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

<a id="openbacktesting-broker-instrumentspec-price-tick"></a>

### price_tick

完整对象：`openbacktesting.broker.InstrumentSpec.price_tick`

<a id="openbacktesting-broker-instrumentspec-currency"></a>

### currency

完整对象：`openbacktesting.broker.InstrumentSpec.currency`

<a id="openbacktesting-broker-instrumentspec-price"></a>

### price

完整对象：`openbacktesting.broker.InstrumentSpec.price`

```python
openbacktesting.broker.InstrumentSpec.price(self, value, *, side=None) -> float
```

请求价格严格校验；执行价格按不利方向规范化。

源码：`src/openbacktesting/broker/instrument.py`。

<a id="openbacktesting-broker-instrumentspec-min-quantity"></a>

### min_quantity

完整对象：`openbacktesting.broker.InstrumentSpec.min_quantity`

<a id="openbacktesting-broker-instrumentspec-quantity"></a>

### quantity

完整对象：`openbacktesting.broker.InstrumentSpec.quantity`

```python
openbacktesting.broker.InstrumentSpec.quantity(self, value, *, floor=False, opening=True) -> float
```

直接请求必须在网格；预算数量可向零取整。

源码：`src/openbacktesting/broker/instrument.py`。

<a id="openbacktesting-broker-instrumentspec-min-notional"></a>

### min_notional

完整对象：`openbacktesting.broker.InstrumentSpec.min_notional`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-broker-instrumentspec-validate-data"></a>

### validate_data

完整对象：`openbacktesting.broker.InstrumentSpec.validate_data`

```python
openbacktesting.broker.InstrumentSpec.validate_data(self, frame)
```

交易行情必须有序、唯一且价格有效，显式tick不得静默修正。

源码：`src/openbacktesting/broker/instrument.py`。

<a id="openbacktesting-broker-instrumentspec-quantity-step"></a>

### quantity_step

完整对象：`openbacktesting.broker.InstrumentSpec.quantity_step`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-broker-instrumentspec-round-price-to-tick"></a>

### round_price_to_tick

完整对象：`openbacktesting.broker.InstrumentSpec.round_price_to_tick`

```python
openbacktesting.broker.InstrumentSpec.round_price_to_tick(self, value: float) -> float
```

按显式 tick 就近归整价格，半 tick 向较高价格归整。

Args:
    value: 有限正价格，不接受布尔值。

Returns:
    通过本品种严格网格校验的有限正 float；不改变撮合舍入政策。

Raises:
    TypeError: value 不是数值或为布尔值。
    ValueError: 缺少 tick、输入非法、结果为零或无法以 float 表示合法网格。

源码：`src/openbacktesting/broker/instrument.py`。

<a id="openbacktesting-broker-orderevent"></a>

## OrderEvent

完整对象：`openbacktesting.broker.OrderEvent`

```python
openbacktesting.broker.OrderEvent(sequence: 'int', bar_index: 'int', timestamp: 'object', phase: 'str', snapshot: 'OrderSnapshot') -> None
```

带时间和阶段的不可变订单事件。

源码：`src/openbacktesting/broker/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `sequence` | `int` |
| `bar_index` | `int` |
| `timestamp` | `object` |
| `phase` | `str` |
| `snapshot` | `OrderSnapshot` |

<a id="openbacktesting-broker-order"></a>

## Order

完整对象：`openbacktesting.broker.Order`

```python
openbacktesting.broker.Order(broker, request, *, group_id=None, kind='entry', eligible=None, sizing=None)
```

稳定订单句柄；request和snapshot为不可变值，cancel可重复调用。

源码：`src/openbacktesting/broker/core.py`。

<a id="openbacktesting-strategy-sizing-equity-fraction"></a>

## equity_fraction

完整对象：`openbacktesting.strategy.sizing.equity_fraction`

```python
openbacktesting.strategy.sizing.equity_fraction(fraction, *, account: openbacktesting.broker.models.AccountSnapshot, reference_price, instrument=None, cost_per_unit=0)
```

权益净名义预算，数量成本占用同一预算；保证金比例不放大此预算。

源码：`src/openbacktesting/strategy/sizing.py`。

<a id="openbacktesting-strategy-sizing-sizingdecision"></a>

## SizingDecision

完整对象：`openbacktesting.strategy.sizing.SizingDecision`

```python
openbacktesting.strategy.sizing.SizingDecision(qty: float, reference_price: float, estimated_cost: float, reason: str | None, budget: float | None = None) -> None
```

预算结果；estimated_cost为给定数量的成本估计，不保证成交价。

源码：`src/openbacktesting/strategy/sizing.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `qty` | `<class 'float'>` |
| `reference_price` | `<class 'float'>` |
| `estimated_cost` | `<class 'float'>` |
| `reason` | `str \| None` |
| `budget` | `float \| None` |

<a id="openbacktesting-strategy-sizing-sizingdecision-budget"></a>

### budget

完整对象：`openbacktesting.strategy.sizing.SizingDecision.budget`

<a id="openbacktesting-strategy-sizing-fixed-quantity"></a>

## fixed_quantity

完整对象：`openbacktesting.strategy.sizing.fixed_quantity`

```python
openbacktesting.strategy.sizing.fixed_quantity(qty: float, *, reference_price, instrument=None, cost_per_unit=0)
```

固定资产数量向零归整；不猜测资金比例。

源码：`src/openbacktesting/strategy/sizing.py`。

<a id="openbacktesting-strategy-sizing-stop-risk"></a>

## stop_risk

完整对象：`openbacktesting.strategy.sizing.stop_risk`

```python
openbacktesting.strategy.sizing.stop_risk(fraction, *, account: openbacktesting.broker.models.AccountSnapshot, reference_price, stop_price, side='buy', instrument=None, cost_per_unit=0)
```

止损风险预算含每单位往返成本估计；跳空可能超过计划损失。

源码：`src/openbacktesting/strategy/sizing.py`。

<a id="openbacktesting-broker-commission"></a>

## Commission

完整对象：`openbacktesting.broker.Commission`

```python
openbacktesting.broker.Commission(fixed: float = 0.0, relative: float = 0.0, per_unit: float = 0.0) -> None
```

每次成交固定额、金额比例和每资产单位费用；比例 0.002 表示 0.2%。

源码：`src/openbacktesting/broker/commission.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `fixed` | `<class 'float'>` |
| `relative` | `<class 'float'>` |
| `per_unit` | `<class 'float'>` |

<a id="openbacktesting-broker-commission-fixed"></a>

### fixed

完整对象：`openbacktesting.broker.Commission.fixed`

Convert a string or number to a floating-point number, if possible.

<a id="openbacktesting-broker-commission-relative"></a>

### relative

完整对象：`openbacktesting.broker.Commission.relative`

Convert a string or number to a floating-point number, if possible.

<a id="openbacktesting-broker-commission-per-unit"></a>

### per_unit

完整对象：`openbacktesting.broker.Commission.per_unit`

Convert a string or number to a floating-point number, if possible.

<a id="openbacktesting-broker-commission-snapshot"></a>

### snapshot

完整对象：`openbacktesting.broker.Commission.snapshot`

```python
openbacktesting.broker.Commission.snapshot(self) -> dict
```

导出带模型版本的独立纯值。

源码：`src/openbacktesting/broker/commission.py`。

<a id="openbacktesting-broker-commission-from-snapshot"></a>

### from_snapshot

完整对象：`openbacktesting.broker.Commission.from_snapshot`

```python
openbacktesting.broker.Commission.from_snapshot(cls, value: collections.abc.Mapping) -> 'Commission'
```

严格恢复完整快照；拒绝未知版本、字段或隐式默认。

源码：`src/openbacktesting/broker/commission.py`。

<a id="openbacktesting-broker-ordersizingsnapshot"></a>

## OrderSizingSnapshot

完整对象：`openbacktesting.broker.OrderSizingSnapshot`

```python
openbacktesting.broker.OrderSizingSnapshot(mode: "Literal['qty', 'amount', 'percent']", source: "Literal['explicit', 'default']", value: 'float', equity: 'float', reference_price: 'float', budget: 'float | None', qty: 'float') -> None
```

提交时冻结的规模依据；预算不保证真实成交金额或费用。

mode 为 qty/amount/percent，source 为 explicit/default；percent 的 value
使用百分数（20 表示 20%），qty 模式的 budget 为 None。

源码：`src/openbacktesting/broker/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `mode` | `Literal['qty', 'amount', 'percent']` |
| `source` | `Literal['explicit', 'default']` |
| `value` | `float` |
| `equity` | `float` |
| `reference_price` | `float` |
| `budget` | `float \| None` |
| `qty` | `float` |

<a id="openbacktesting-broker-closedtradestats"></a>

## ClosedTradeStats

完整对象：`openbacktesting.broker.ClosedTradeStats`

```python
openbacktesting.broker.ClosedTradeStats(closed_count: 'int' = 0, win_count: 'int' = 0, loss_count: 'int' = 0, even_count: 'int' = 0, winning_profit: 'float' = 0.0, losing_amount: 'float' = 0.0, net_profit: 'float' = 0.0, average_profit: 'float | None' = None, win_rate: 'float | None' = None) -> None
```

截至读取时的关闭片段累计；费用已分摊，不含未平仓损益。

次数按关闭片段而非 trade_id 计数，胜负按净损益严格正负分类。
losing_amount 是非负亏损额；空记录的平均净损益和 0–1 胜率为 None。
值不携带运行对象，保存的快照不受后续成交影响。

源码：`src/openbacktesting/broker/models.py`。

字段由定义提取；构造签名给出默认值，字段语义见对应使用指南。

| 字段 | 类型 |
| --- | --- |
| `closed_count` | `int` |
| `win_count` | `int` |
| `loss_count` | `int` |
| `even_count` | `int` |
| `winning_profit` | `float` |
| `losing_amount` | `float` |
| `net_profit` | `float` |
| `average_profit` | `float \| None` |
| `win_rate` | `float \| None` |

<a id="openbacktesting-broker-closedtradestats-even-count"></a>

### even_count

完整对象：`openbacktesting.broker.ClosedTradeStats.even_count`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-broker-closedtradestats-closed-count"></a>

### closed_count

完整对象：`openbacktesting.broker.ClosedTradeStats.closed_count`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-broker-closedtradestats-win-count"></a>

### win_count

完整对象：`openbacktesting.broker.ClosedTradeStats.win_count`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-broker-closedtradestats-winning-profit"></a>

### winning_profit

完整对象：`openbacktesting.broker.ClosedTradeStats.winning_profit`

Convert a string or number to a floating-point number, if possible.

<a id="openbacktesting-broker-closedtradestats-loss-count"></a>

### loss_count

完整对象：`openbacktesting.broker.ClosedTradeStats.loss_count`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

<a id="openbacktesting-broker-closedtradestats-average-profit"></a>

### average_profit

完整对象：`openbacktesting.broker.ClosedTradeStats.average_profit`

<a id="openbacktesting-broker-closedtradestats-win-rate"></a>

### win_rate

完整对象：`openbacktesting.broker.ClosedTradeStats.win_rate`

<a id="openbacktesting-broker-closedtradestats-net-profit"></a>

### net_profit

完整对象：`openbacktesting.broker.ClosedTradeStats.net_profit`

Convert a string or number to a floating-point number, if possible.

<a id="openbacktesting-broker-closedtradestats-losing-amount"></a>

### losing_amount

完整对象：`openbacktesting.broker.ClosedTradeStats.losing_amount`

Convert a string or number to a floating-point number, if possible.

<a id="openbacktesting-engine-trade-entry-bar"></a>

## entry_bar 实例字段

Trade.entry_bar 保留为批次实例字段。对应结果表保留 EntryBar/EntryPrice/ExitBar/ExitPrice；活跃批次退出字段为空。

<a id="openbacktesting-engine-trade-entry-price"></a>

## entry_price 实例字段

Trade.entry_price 保留为批次实例字段。对应结果表保留 EntryBar/EntryPrice/ExitBar/ExitPrice；活跃批次退出字段为空。

<a id="openbacktesting-engine-trade-exit-bar"></a>

## exit_bar 实例字段

Trade.exit_bar 保留为批次实例字段。对应结果表保留 EntryBar/EntryPrice/ExitBar/ExitPrice；活跃批次退出字段为空。

<a id="openbacktesting-engine-trade-exit-price"></a>

## exit_price 实例字段

Trade.exit_price 保留为批次实例字段。对应结果表保留 EntryBar/EntryPrice/ExitBar/ExitPrice；活跃批次退出字段为空。
