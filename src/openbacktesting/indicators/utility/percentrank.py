"""ta.percentrank：固定因果序列契约。"""

from ..calculus import clean


def compute(*, source, length):
    return (100 * clean(source).rolling(length).rank(method="max", pct=True)).rename("percentrank")
