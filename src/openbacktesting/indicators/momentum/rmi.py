"""ta.rmi：独立公式与固定初始化契约。"""

from ..calculus import clean, strength


def compute(*, close, length, momentum):
    return strength(clean(close).diff(momentum), length).rename("rmi")
