"""Machine-learning research tutorial (not a recommended template): features, one-time training, and rolling training.

Bundled EURUSD hourly data; requires scikit-learn (test extra). Read the native-backtest and data-column interfaces first.
Labels use returns over the next 48 bars, which need not span two calendar days; unknown labels at the end of training data are dropped.
Random-split accuracy demonstrates classification only, not time-series out-of-sample performance; temporal splits, gaps, and feature validity require independent evaluation.
main runs a classification demonstration and two full backtests, predicting every bar and retraining every 20 bars; this example takes longer than the others.
0.02% commission, 20:1 leverage, and 20% of available funds per order; predictions use an ordinary log array, retaining open positions at the end.
"""

import numpy as np
import pandas as pd

from openbacktesting import Backtest, Strategy
from openbacktesting.indicators import compute
from openbacktesting.test import EURUSD

N_TRAIN = 400


def classifier_type():
    try:
        from sklearn.neighbors import KNeighborsClassifier
    except ImportError as exc:
        raise RuntimeError("The ML tutorial requires an extra dependency: pip install 'openbacktesting[test]'") from exc
    return KNeighborsClassifier


def get_X(data):
    """Extract the feature matrix."""
    return data.filter(like="X").values


def get_y(data):
    """Classify returns 48 bars ahead; keep unknown trailing labels as NaN."""
    y = data.Close.pct_change(48).shift(-48)
    y[y.between(-0.004, 0.004)] = 0
    y[y > 0] = 1
    y[y < 0] = -1
    return y


def get_clean_Xy(df):
    """Remove only training rows whose labels are still unknown."""
    X = get_X(df)
    y = get_y(df).values
    isnan = np.isnan(y)
    X = X[~isnan]
    y = y[~isnan]
    return (X, y)


class MLTrainOnceStrategy(Strategy):
    price_delta = 0.004

    def init(self):
        self.clf = classifier_type()(7)
        df = self.data.df.iloc[:N_TRAIN]
        X, y = get_clean_Xy(df)
        self.clf.fit(X, y)
        # Predictions do not exist yet and cannot be registered as read-only warmup indicators; record them by absolute bar position.
        self.forecasts = np.full(len(self.data), np.nan)

    def next(self):
        if len(self.data) < N_TRAIN:
            return
        high, low, close = (self.data.High[-1], self.data.Low[-1], self.data.Close[-1])
        current_time = self.data.index[-1]
        X = get_X(self.data.df.iloc[-1:])
        forecast = self.clf.predict(X)[0]
        self.forecasts[len(self.data) - 1] = forecast
        upper, lower = close * (1 + np.r_[1, -1] * self.price_delta)
        if forecast == 1 and (not self.position.is_long):
            self.buy(
                percent=20,
                tp=upper,
                sl=lower,
            )
        elif forecast == -1 and (not self.position.is_short):
            self.sell(
                percent=20,
                tp=lower,
                sl=upper,
            )
        for trade in self.trades:
            if current_time - trade.entry_time > pd.Timedelta("2 days"):
                if trade.is_long:
                    trade.sl = max(trade.sl, low)
                else:
                    trade.sl = min(trade.sl, high)


class MLWalkForwardStrategy(MLTrainOnceStrategy):
    def next(self):
        if len(self.data) < N_TRAIN:
            return
        if len(self.data) % 20:
            return super().next()
        df = self.data.df[-N_TRAIN:]
        X, y = get_clean_Xy(df)
        self.clf.fit(X, y)
        super().next()


def prepare_data():
    # Build features from current and historical data only; synthetic sentiment demonstrates an additional column.
    data = EURUSD.copy()
    close = data.Close.values
    sma10 = compute("ta.sma", data, parameters={"length": 10}).s
    sma20 = compute("ta.sma", data, parameters={"length": 20}).s
    sma50 = compute("ta.sma", data, parameters={"length": 50}).s
    sma100 = compute("ta.sma", data, parameters={"length": 100}).s
    # Offline features have no Strategy instance; reuse built-in algorithms through public compute.
    # HLC3 and ddof=1 preserve the original feature definition rather than using default close prices and population standard deviation.
    bands = compute(
        "ta.bbands",
        data.assign(HLC3=(data.High + data.Low + data.Close) / 3),
        inputs={"close": "HLC3"},
        parameters={"length": 20, "std": 2.0, "ddof": 1},
    )
    upper, lower = bands["upper"].s, bands["lower"].s
    data["X_SMA10"] = (close - sma10) / close
    data["X_SMA20"] = (close - sma20) / close
    data["X_SMA50"] = (close - sma50) / close
    data["X_SMA100"] = (close - sma100) / close
    data["X_DELTA_SMA10"] = (sma10 - sma20) / close
    data["X_DELTA_SMA20"] = (sma20 - sma50) / close
    data["X_DELTA_SMA50"] = (sma50 - sma100) / close
    data["X_MOM"] = data.Close.pct_change(periods=2)
    data["X_BB_upper"] = (upper - close) / close
    data["X_BB_lower"] = (lower - close) / close
    data["X_BB_width"] = (upper - lower) / close
    data["X_Sentiment"] = ~data.index.to_series().between("2017-09-27", "2017-12-14")
    data["X_day"] = data.index.dayofweek
    data["X_hour"] = data.index.hour
    data = data.dropna().astype(float)
    return data


def main():
    classifier = classifier_type()
    from sklearn.model_selection import train_test_split

    data = prepare_data()
    X, y = get_clean_Xy(data)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=0)
    clf = classifier(7)
    clf.fit(X_train, y_train)
    accuracy = np.mean(y_test == clf.predict(X_test))
    print("Random-split classification accuracy (not time-series out-of-sample validation):", accuracy)
    once = Backtest(data, MLTrainOnceStrategy, commission=0.0002, margin=0.05).run()
    rolling = Backtest(data, MLWalkForwardStrategy, commission=0.0002, margin=0.05).run()
    print("One-time training:", once)
    print("Rolling training:", rolling)
    return once, rolling


if __name__ == "__main__":
    main()
