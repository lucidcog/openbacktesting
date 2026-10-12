"""ta.shift：固定因果序列契约。"""

from ..calculus import clean


def compute(*, source, length):
    return clean(source).shift(length).rename("shift")
