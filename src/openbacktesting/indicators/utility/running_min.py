"""ta.running_min：固定因果序列契约。"""

from ..calculus import clean


def compute(*, source):
    return clean(source).cummin().rename("running_min")
