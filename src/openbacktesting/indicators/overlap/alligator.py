"""ta.alligator: Independent formula with a fixed initialization contract."""

import pandas as pd

from ..calculus import average, clean


def compute(*, high, low, jaw, teeth, lips):
    middle = (clean(high) + clean(low)) / 2
    j = average(middle, jaw, alpha=1 / jaw)
    t = average(middle, teeth, alpha=1 / teeth)
    l = average(middle, lips, alpha=1 / lips)
    return pd.DataFrame({"jaw": j, "teeth": t, "lips": l})
