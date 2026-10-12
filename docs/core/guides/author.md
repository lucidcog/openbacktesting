# 策略作者与生命周期

声明 inputs 后，宿主可用[参数实验](optimizer.md)扫描其中一部分，其他值固定为当前配置。实验入口不采集日志或绘图；策略应避免依赖跨运行的模块全局或外部可变状态。

## 用户脚本：声明策略与回测设置

用户通过 `@backtest(...)` 为策略类声明默认回测设置。加载脚本只定义策略；框架从当前图表注入行情、周期、时区与品种规格，再创建独立回测会话：

[完整源码](../../../examples/strategies/ema_macd.py)

每个作者模块必须只有一个本模块定义、直接装饰的具体 `Strategy` 子类；别名不重复计数，导入类和未重新装饰的派生类不是入口。装饰器保持原类身份；显式重新装饰派生类会使用自己的设置默认值，不继承父声明。

`@backtest` 接受账户、成本、执行政策、统计基准和默认数量，类似策略默认属性；`inputs` 定义策略算法参数。`self.timeframe` 提供本次图表周期，不能通过类字段、inputs 或运行参数覆盖。完整边界见[宿主运行](runtime.md)。

`init()` 可以访问完整数据并预计算指标；`next()` 看到当前逐步展开的历史，最新价格为 `self.close[-1]`，旧写法 `self.data.Close[-1]` 继续可用。指标登记不等于 Pine 指标实现，不应在预计算中使用未来信息。

## 平铺回测设置

`@backtest()` 的全部参数均为命名参数；分类选项使用从 `openbacktesting` 导入的枚举。作者入口不接受裸字符串、字典或 `Commission`、`DefaultOrderSize`、`Slippage` 配置对象；这些模型保留给低层 `Backtest`。

```python
from openbacktesting import CommissionType, QuantityType, Strategy, backtest

@backtest(
    commission_type=CommissionType.PERCENT,
    commission_value=0.2,
    default_qty_type=QuantityType.PERCENT_OF_EQUITY,
    default_qty_value=10,
)
class MyStrategy(Strategy):
    def init(self):
        pass

    def next(self):
        if len(self.data) == 2:
            self.buy()
```

上述佣金为成交金额的 0.2%，默认数量为请求时权益的 10% 按 Close 换算。`self.buy()` 使用默认数量，`self.buy(qty=1)` 使用显式资产数量，`self.buy(amount=500)` 使用名义金额，`self.buy(percent=20)` 使用权益的 20%。三者互斥，显式参数覆盖默认；只减仓必须显式给 qty，OCO 成员必须各自给一种规模，不继承默认。数量预算不预留费用，不保证未来成交；过小预算报错。

| 参数                 | 默认值                      | 含义与范围                                         |
| -------------------- | --------------------------- | -------------------------------------------------- |
| `cash`               | `10000`                     | 初始账户金额，有限且大于 0                         |
| `spread`             | `0.0`                       | 价差小数比例，[0,1)，0.001 为 0.1%                 |
| `commission_type`    | `CommissionType.PERCENT`    | 佣金模式，见下表                                   |
| `commission_value`   | `0.0`                       | 百分数 [-10,10) 或非负账户金额                     |
| `risk_free_rate`     | `0.0`                       | 统计无风险年利率小数，(-1,1)，0.02 为 2%           |
| `default_qty_type`   | `QuantityType.FIXED`        | 固定资产数量或权益百分数                           |
| `default_qty_value`  | `None`                      | None 禁用默认数量；固定数量 >0；权益百分数 (0,100] |
| `margin`             | `1.0`                       | 保证金比例，(0,1]，0.5 对应最大 2 倍保证金杠杆     |
| `execution_timing`   | `ExecutionTiming.NEXT_OPEN` | 下一根处理或本根收盘处理新增无条件市价单           |
| `slippage_type`      | `SlippageType.BPS`          | 固定价格距离或基点                                 |
| `slippage_value`     | `0.0`                       | 非负滑点距离，0 表示无滑点                         |
| `allow_short`        | `True`                      | 是否允许新增空头，严格 bool                        |
| `max_gross_exposure` | `None`                      | 可选总名义暴露／权益上限，有限且 >0                |
| `hedging`            | `False`                     | 是否允许多空批次并存，严格 bool                    |
| `exclusive_orders`   | `False`                     | 沿用互斥订单政策，严格 bool                        |
| `end_policy`         | `EndPolicy.MARK_TO_MARKET`  | 期末估值或清算实际持仓                             |

所有数值必须有限，拒绝 bool 冒充数值；仅 `default_qty_value`、`max_gross_exposure` 允许 None。

| 枚举成员                           | JSON 值               | 数值单位／行为                                           |
| ---------------------------------- | --------------------- | -------------------------------------------------------- |
| `CommissionType.PERCENT`           | `percent`             | 成交金额百分数；0.2 = 0.2%；负值表示返佣                 |
| `CommissionType.CASH_PER_ORDER`    | `cash_per_order`      | 每次实际 Fill 的固定账户金额，不按订单登记次数收取       |
| `CommissionType.CASH_PER_CONTRACT` | `cash_per_contract`   | 每实际资产单位的账户金额；合约乘数为 1                   |
| `QuantityType.FIXED`               | `fixed`               | 固定资产数量                                             |
| `QuantityType.PERCENT_OF_EQUITY`   | `percent_of_equity`   | 请求时权益百分数；10 = 10%                               |
| `SlippageType.FIXED`               | `fixed`               | 固定价格距离                                             |
| `SlippageType.BPS`                 | `bps`                 | 基点；1 = 0.01%                                          |
| `ExecutionTiming.NEXT_OPEN`        | `next_open`           | 最早下一根处理                                           |
| `ExecutionTiming.SAME_CLOSE`       | `same_close`          | 本根收盘处理新增无条件市价单；条件单和保护单保留因果限制 |
| `EndPolicy.MARK_TO_MARKET`         | `mark_to_market`      | 撤销挂单并保留持仓估值                                   |
| `EndPolicy.CLOSE_AT_LAST_CLOSE`    | `close_at_last_close` | 撤销挂单，再按末 Close 清算实际持仓并计成本              |

只有佣金 PERCENT 和数量 PERCENT_OF_EQUITY 使用百分数；spread、margin、risk_free_rate 与 max_gross_exposure 继续使用原小数／倍数单位。作者一次只能选择一种佣金模式；复合费用或 callable 使用低层 Backtest。完整运行与覆盖见[设置教程](../../../examples/advanced/strategy_settings.py)，订单边界见[交易指南](trading.md)。

## 图表时间

在 `next()` 中读取 `self.data_index[-1]`，得到当前 bar 按图表时区表示的带时区时间；`self.data.index` 和 `self.df.index` 使用相同解释。`.hour`、`.date()`、`.weekday()` 可以直接用于当地日历条件，转换在策略构造和 init 前完成，既有可见范围不变。例如底层 `01:00 UTC` 在上海图表中为 `09:00+08:00`，策略直接读取的小时为 `9`。

切换图表时区后需重新运行；依赖当地时间的交易逻辑允许改变结果。纽约夏令时回拨期间两个 `01:30` 的偏移不同，仍是不同的 bar，不要去掉时区后按墙钟去重。这里读取的是 bar 时间标签，不是系统执行时间，也不据此推断交易所开盘或月线边界。固定市场逻辑可显式调用 `tz_convert("America/New_York")`。

可运行示例见[图表上下文教程](../../../examples/advanced/chart_context.py)，它同时演示时区传入、当地小时下单、重复小时和按图表日界统计。

## 策略日志

在作者回调中使用 `self.log.info(message)`、`warning(message)`、`error(message)`，三者只接收字符串并返回 None。可用 f-string 格式化；中文、空字符串、换行和重复消息原样保留。error 只记录级别，需要终止时显式 raise。完整作者示例：

[完整源码](../../../examples/strategies/strategy_logs.py)

日志自动记录 UTC 系统时间、当前输入 bar 时间标签、零起点 `bar_index`、实际调用的文件及从 1 开始的源码行号。init/on_finish 没有当前 bar，其 bar 字段为 None；on_start 绑定第 0 根。辅助函数中的日志指向辅助函数实际调用日志的行；不记录整个调用栈，也不读源码文本。位置不可取得时文件与行号同时为 None。

`log` 是保留名，不能用作类字段、方法、Input 字段或原生参数，也不能赋值/删除 `self.log`；Input 的展示标题仍可为“log”。构造函数、回调外及运行结束后不支持写日志，不承诺作者线程/异步写入。日志不受绘图开关或全局 Python logging 配置影响，不自动捕获 print/warnings，也不写入终端。消费和字段说明见[日志结果](results.md#策略日志)。
