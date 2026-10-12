"""ta.valuewhen：固定因果序列契约。"""

from collections import deque

import numpy as np
import pandas as pd

from ..calculus import clean
from ..calculus import condition as validate_condition


def compute(*, condition, source, occurrence):
    condition = validate_condition(condition, "ta.valuewhen")
    source = clean(source)
    result = np.full(len(source), np.nan)
    events = deque(maxlen=occurrence + 1)
    for i, value in enumerate(condition):
        if not np.isfinite(value):
            events.clear()
        else:
            if value == 1:
                events.append(source.iloc[i])
            if len(events) > occurrence:
                result[i] = events[0]
    return pd.Series(result, index=source.index, name="valuewhen")
