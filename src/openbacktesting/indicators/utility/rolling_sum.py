"""ta.rolling_sum：固定因果序列契约。"""

from ..calculus import clean


def compute(*, source, length):
    return clean(source).rolling(length).sum().rename("rolling_sum")
