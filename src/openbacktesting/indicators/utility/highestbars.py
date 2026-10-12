"""ta.highestbars: Fixed causal sequence contract."""

from collections import deque

import numpy as np
import pandas as pd

from ..calculus import clean


def compute(*, source, length):
    source = clean(source)
    values = source.to_numpy()
    result = np.full(len(source), np.nan)
    queue = deque()
    last_missing = -1
    for i, value in enumerate(values):
        if not np.isfinite(value):
            last_missing = i
            queue.clear()
            continue
        while queue and values[queue[-1]] <= value:
            queue.pop()
        queue.append(i)
        if queue[0] <= i - length:
            queue.popleft()
        if i >= length - 1 and i - last_missing >= length:
            result[i] = queue[0] - i
    return pd.Series(result, index=source.index, name="highestbars")
