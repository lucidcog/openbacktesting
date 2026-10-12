"""到期、混合规模原子入场OCO、保护组与百分比跟踪；每次成交滑点0.5。

同bar双触发OCO按提交顺序决定并留下歧义诊断；跟踪价在收盘更新，下一根生效。
这只是确定性OHLC政策，不表示可以推断真实盘中路径。
"""

import pandas as pd
from openbacktesting import SlippageType, Strategy, backtest
from openbacktesting.broker import OrderRequest


@backtest(slippage_type=SlippageType.FIXED, slippage_value=0.5)
class ManagedOrders(Strategy):
    def init(self):
        self.reference = self.ta.sma(self.close, length=2)
        # 这里只记录意图；提交时才按同一账户与 Close 换算。
        self.long_entry = OrderRequest(side="buy", percent=1, stop=105, sl=90, tp=130)
        self.short_entry = OrderRequest(side="sell", amount=100, stop=95)

    def next(self):
        bar = len(self.data) - 1
        if bar == 2:
            self.buy(qty=1, limit=80, valid_bars=1)
            self.buy(qty=1, limit=80, expires_at=self.data_index[-1] + pd.Timedelta(days=1))
        elif bar == 3:
            self.entries = self.submit_oco(
                first=self.long_entry,
                second=self.short_entry,
            )
        elif bar == 4:
            self.trades[0].set_trailing_stop(amount=10)
            self.trades[0].set_trailing_stop(percent=0.1)
