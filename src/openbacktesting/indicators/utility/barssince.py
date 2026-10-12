"""ta.barssince: Fixed causal sequence contract."""

import numpy as np
import pandas as pd

from ..calculus import condition as validate_condition


def compute(*, condition):
    condition = validate_condition(condition, "ta.barssince")
    result = np.full(len(condition), np.nan)
    last = None
    for i, value in enumerate(condition):
        if not np.isfinite(value):
            last = None
        else:
            if value == 1:
                last = i
            if last is not None:
                result[i] = i - last
    return pd.Series(result, index=condition.index, name="barssince")
