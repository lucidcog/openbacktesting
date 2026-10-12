"""记录三级日志及当前 bar；由宿主取回时间和源码位置。

使用宿主提供的历史行情，无额外依赖、不下单；仓位和费用不参与示例。
error 只记录级别；打开“演示失败”参数才显式抛出异常。
"""

from openbacktesting import Strategy, backtest, inputs


@backtest()
class StrategyLogs(Strategy):
    fail = inputs.bool(False, title="演示失败")

    def init(self):
        # 初始化日志没有当前 bar，仍记录系统时间与实际调用代码行。
        self.average = self.ta.sma(self.close, length=3)
        self.log.info("初始化完成")

    def next(self):
        self.log.info(
            f"bar={self.bar_index}, close={self.close[-1]:.2f}, sma={self.average[-1]:.2f}"
        )
        if self.bar_state.is_first:
            self.log.warning("第一根没有上一根价格")
            self.log.error("演示 error 级别，回测继续")
            if self.fail:
                raise ValueError("演示显式失败")

    def on_finish(self, summary):
        self.log.info(f"结束原因：{summary.reason}")
