"""机器学习研究教程（非推荐模板）：特征列、一次训练与滚动训练。

随包 EURUSD 小时线；运行需要 scikit-learn（test extra）。先阅读原生回测和数据列接口。
标签为未来 48 根收益，未必是连续两个日历日；训练样本末尾未知标签会被剔除。
随机拆分准确率只演示分类，不是时序样本外证据；时序拆分、间隔与特征有效性仍待独立评估。
main 执行分类演示和两次完整回测，逐 bar 预测、每 20 根滚动重训，较其他例子耗时。
手续费 0.02%、20:1 杠杆、每次 20% 可用资金；预测写入普通日志数组，保留期末未平仓语义。
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
        raise RuntimeError("ML 教程需要额外依赖：pip install 'openbacktesting[test]'") from exc
    return KNeighborsClassifier


def get_X(data):
    """提取特征矩阵。"""
    return data.filter(like="X").values


def get_y(data):
    """48 根之后的收益分类；末尾未知标签保留 NaN。"""
    y = data.Close.pct_change(48).shift(-48)
    y[y.between(-0.004, 0.004)] = 0
    y[y > 0] = 1
    y[y < 0] = -1
    return y


def get_clean_Xy(df):
    """仅移除标签尚未知的训练行。"""
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
        # 预测尚未产生，不能注册成参与预热的只读指标；按绝对 bar 位置记录。
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
    # 只使用当前及历史行情构造特征；合成 sentiment 仅用于展示额外列。
    data = EURUSD.copy()
    close = data.Close.values
    sma10 = compute("ta.sma", data, parameters={"length": 10}).s
    sma20 = compute("ta.sma", data, parameters={"length": 20}).s
    sma50 = compute("ta.sma", data, parameters={"length": 50}).s
    sma100 = compute("ta.sma", data, parameters={"length": 100}).s
    # 离线特征没有 Strategy 实例，通过公开 compute 复用内置算法。
    # HLC3 与 ddof=1 保留原特征定义，不改用默认收盘价和总体标准差。
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
    print("随机拆分分类准确率（不是时序样本外验证）：", accuracy)
    once = Backtest(data, MLTrainOnceStrategy, commission=0.0002, margin=0.05).run()
    rolling = Backtest(data, MLWalkForwardStrategy, commission=0.0002, margin=0.05).run()
    print("一次训练：", once)
    print("滚动训练：", rolling)
    return once, rolling


if __name__ == "__main__":
    main()
