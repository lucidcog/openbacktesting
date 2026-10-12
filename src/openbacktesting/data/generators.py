"""从 lib 迁入的既有实现：random_ohlc_data。"""

from __future__ import annotations

from collections.abc import Generator

import pandas as pd

from openbacktesting.helpers import _set_legacy_module


def random_ohlc_data(
    example_data: pd.DataFrame, *, frac=1.0, random_state: int | None = None
) -> Generator[pd.DataFrame, None, None]:
    """迭代生成保留基本行情结构的随机样例，不代表真实市场预测。


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
    """

    def shuffle(x):
        return x.sample(frac=frac, replace=frac > 1, random_state=random_state)

    if len(example_data.columns.intersection({"Open", "High", "Low", "Close"})) != 4:
        raise ValueError(
            "`data` must be a pandas.DataFrame with columns 'Open', 'High', 'Low', 'Close'"
        )
    while True:
        df = shuffle(example_data)
        df.index = example_data.index
        padding = df.Close - df.Open.shift(-1)
        gaps = shuffle(example_data.Open.shift(-1) - example_data.Close)
        deltas = (padding + gaps).shift(1).fillna(0).cumsum()
        for key in ("Open", "High", "Low", "Close"):
            df[key] += deltas
        yield df


_set_legacy_module(random_ohlc_data, "openbacktesting.lib")
