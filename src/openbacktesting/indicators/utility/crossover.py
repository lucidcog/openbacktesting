"""ta.crossover：固定因果序列契约。"""

from ..calculus import clean


def compute(*, left, right):
    left, right = clean(left), clean(right)
    a, b = left.shift(1), right.shift(1)
    up = (left > right) & (a <= b)
    valid = left.notna() & right.notna() & a.notna() & b.notna()
    return (up).astype(float).where(valid).rename("crossover")
