"""Daily/weekly RSI resampling: understand native backtests and pandas date indexes, then explicitly run main.

Bundled GOOG daily data, with no additional dependencies; d_rsi/w_rsi are daily/weekly periods and level is the entry threshold.
W-FRI uses right labels on Fridays and forward-fills completed-period results into daily data; input must be ordered and calendar-aligned.
The GOOG index is timezone-naive; this example does not handle intraday exchange timezones or missing trading days and does not establish Pine multi-timeframe equivalence.
Built-in RSI and moving-average filters, 0.2% commission, and an 8% stop; no forced end-of-run liquidation. Print statistics for one backtest.
"""

from openbacktesting import Backtest, Strategy
from openbacktesting.indicators import compute
from openbacktesting.lib import resample_apply
from openbacktesting.test import GOOG


def resampled_rsi(close, length):
    """Weekly data uses a separate date index and the same built-in RSI through public compute.

    self.ta is bound to the main backtest calendar and cannot directly register weekly data of a different length;
    resample_apply aligns results to daily data and registers an indicator whose visibility follows the cursor.
    """
    return compute("ta.rsi", close.to_frame("Close"), parameters={"length": length}).s


class System(Strategy):
    d_rsi = 30
    w_rsi = 30
    level = 70

    def init(self):
        self.ma10 = self.ta.sma(self.close, length=10)
        self.ma20 = self.ta.sma(self.close, length=20)
        self.ma50 = self.ta.sma(self.close, length=50)
        self.ma100 = self.ta.sma(self.close, length=100)
        self.daily_rsi = self.ta.rsi(self.close, length=self.d_rsi)
        self.weekly_rsi = resample_apply("W-FRI", resampled_rsi, self.close, self.w_rsi)

    def next(self):
        price = self.close[-1]
        if (
            not self.position
            and all(
                line.valid[-1]
                for line in (
                    self.daily_rsi,
                    self.weekly_rsi,
                    self.ma10,
                    self.ma20,
                    self.ma50,
                    self.ma100,
                )
            )
            and self.daily_rsi[-1] > self.level
            and (self.weekly_rsi[-1] > self.level)
            and (self.weekly_rsi[-1] > self.daily_rsi[-1])
            and (self.ma10[-1] > self.ma20[-1] > self.ma50[-1] > self.ma100[-1])
            and (price > self.ma10[-1])
        ):
            self.buy(
                percent=95,
                sl=0.92 * price,
            )
        elif self.ma10.valid[-1] and price < 0.98 * self.ma10[-1]:
            self.position.close()


def main():
    stats = Backtest(GOOG, System, commission=0.002).run()
    print(stats)
    return stats


if __name__ == "__main__":
    main()
