"""仅对稳定可编码的行情和宿主声明计算实验身份。"""

import hashlib
import platform
from importlib.metadata import version

import pandas as pd

from openbacktesting.optimizer.models import ExecutionIdentity, digest


def execution_identity(data, identity, backtest):
    if not isinstance(identity, ExecutionIdentity):
        raise TypeError("optimizer: identity 必须为 ExecutionIdentity")
    if not isinstance(data, pd.DataFrame) or not isinstance(data.index, pd.DatetimeIndex):
        raise TypeError("optimizer: data 必须是日期索引 DataFrame")
    if not data.columns.is_unique or any(type(c) is not str for c in data.columns):
        raise ValueError("optimizer: 行情列名必须为唯一字符串")
    for dtype in data.dtypes:
        if dtype.kind not in "biufMm" or str(dtype) == "object":
            raise TypeError("optimizer: 行情只能含数值、布尔和时间列")
    hashes = pd.util.hash_pandas_object(data, index=True).to_numpy().astype("<u8").tobytes()
    data_hash = hashlib.sha256(hashes).hexdigest()
    return {
        "identityVersion": 1,
        "source": identity.strategy_sha256,
        "dependencies": identity.dependencies_sha256,
        "data": digest(
            {
                "hash": data_hash,
                "columns": list(data.columns),
                "dtypes": list(map(str, data.dtypes)),
                "index": str(data.index.dtype),
                "indexName": data.index.name,
            }
        ),
        "environment": {
            "python": platform.python_version(),
            **{
                name: version(name)
                for name in ("openbacktesting", "numpy", "pandas", "pandas-ta-classic")
            },
        },
        "backtest": backtest,
    }
