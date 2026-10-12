"""最近 length 个有限观测的众数；并列取最小，状态随窗口有界。"""

from collections import Counter, deque
from heapq import heapify, heappop, heappush
from math import isfinite

import numpy as np
import pandas as pd


class _ModeWindow:
    def __init__(self, length):
        self.length = length
        self.queue = deque()
        self.counts = Counter()
        self.heap = []

    def _change(self, value, delta):
        count = self.counts[value] + delta
        if count:
            self.counts[value] = count
            heappush(self.heap, (-count, value))
        else:
            del self.counts[value]

    def add(self, value):
        self.queue.append(value)
        self._change(value, 1)
        if len(self.queue) > self.length:
            self._change(self.queue.popleft(), -1)
        if len(self.heap) > 4 * self.length:
            self.heap = [(-count, value) for value, count in self.counts.items()]
            heapify(self.heap)
        while -self.heap[0][0] != self.counts.get(self.heap[0][1], 0):
            heappop(self.heap)

    def value(self):
        return self.heap[0][1] if len(self.queue) == self.length else np.nan


def compute(*, close, length):
    window = _ModeWindow(length)
    result = np.full(len(close), np.nan)
    for i, value in enumerate(close):
        if isfinite(value):
            window.add(value)
        result[i] = window.value()
    return pd.Series(result, index=close.index, name="mode")
