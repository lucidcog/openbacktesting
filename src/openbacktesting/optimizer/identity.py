"""Calculate experiment identity only for stably encodable market data and host declarations."""

import hashlib
import platform
from importlib.metadata import version

import pandas as pd

from openbacktesting.optimizer.models import ExecutionIdentity, digest


def execution_identity(data, identity, backtest):
    if not isinstance(identity, ExecutionIdentity):
        raise TypeError("optimizer: identity must be an ExecutionIdentity")
    if not isinstance(data, pd.DataFrame) or not isinstance(data.index, pd.DatetimeIndex):
        raise TypeError("optimizer: data must be a DataFrame with a datetime index")
    if not data.columns.is_unique or any(type(c) is not str for c in data.columns):
        raise ValueError("optimizer: market-data column names must be unique strings")
    for dtype in data.dtypes:
        if dtype.kind not in "biufMm" or str(dtype) == "object":
            raise TypeError("optimizer: market data may contain only numeric, boolean, and datetime columns")
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
