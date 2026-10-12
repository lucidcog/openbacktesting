"""ta.running_max：固定因果序列契约。"""

from ..calculus import clean


def compute(*, source):
    return clean(source).cummax().rename("running_max")
