"""逐项体验指标：同一份离线数据，登记一个指标，读取各输出通道。

附加输入只用于演示绑定，不代表真实基准或交易所周期。无交易、无手续费，
required_outputs=[] 使稀疏输出也能被观察；读取前逐通道检查 valid。
"""

import argparse

import numpy as np
from openbacktesting import Backtest, Strategy
from openbacktesting.indicators import describe
from openbacktesting.test import GOOG


def make_data():
    data = GOOG.copy()
    data["source"] = data.Close
    data["benchmark"] = data.Close.shift(1)  # 示例序列，请换成同日历真实基准
    data["periods"] = 10.0
    data["fast"] = data.Close.rolling(3).mean()
    data["slow"] = data.Close.rolling(10).mean()
    data["left"] = data["fast"]
    data["right"] = data["slow"]
    data["condition"] = (data.Close > data.Open).astype(float)
    data["trend"] = data["condition"]
    data["signal"] = data.Close.pct_change() * 100
    data["anchor"] = (np.arange(len(data)) % 20 == 0).astype(float)
    return data


def main(indicator="ta.ema"):
    spec = describe(indicator)
    if spec.status != "available":
        raise ValueError(f"{indicator}: {spec.reason}")

    class ObserveIndicator(Strategy):
        def init(self):
            self.value = getattr(self.ta, indicator.removeprefix("ta."))(required_outputs=[])
            self.latest = {}

        def next(self):
            for channel in spec.outputs:
                handle = self.value if len(spec.outputs) == 1 else self.value[channel]
                if handle.valid[-1]:
                    self.latest[channel] = float(handle[-1])

    result = Backtest(make_data(), ObserveIndicator).run()
    print(result[["Return [%]", "# Trades"]])
    print(indicator, result["_strategy"].latest)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--indicator", default="ta.ema")
    main(parser.parse_args().indicator)
