"""只读执行观察：独立顺序、有效价格区间和批次极值。"""

from openbacktesting.broker.models import record


def _update_extrema(state, bar_index, favorable, adverse):
    # 初值为零，严格比较既排除负幅度，也保留并列极值的首次位置。
    if favorable > state["mfe"]:
        state["mfe"], state["mfeBar"] = favorable, bar_index
    if adverse > state["mae"]:
        state["mae"], state["maeBar"] = adverse, bar_index


class Observations:
    def __init__(self):
        self.rows = []
        self.lots = {}
        self.closed = {}
        self.changed_bar = -1

    def sample(
        self,
        broker,
        price,
        phase,
        *,
        ordered=True,
        coverage="complete_under_bar_model",
        facts=None,
        range_eligible=False,
    ):
        if facts is None:
            position = broker.ledger.position(broker.trades, price)
            facts = record(broker.ledger.account(position, broker.margin)) | record(position)
        row = {
            "observationId": f"observation-{len(self.rows) + 1}",
            "observationSequence": len(self.rows) + 1,
            "barIndex": broker._i,
            "phase": phase,
            "price": price,
            "fillSequence": broker.fills[-1].sequence if broker.fills else 0,
            "ordered": ordered,
            "coverage": coverage,
            "rangeEligible": range_eligible,
            **facts,
        }
        self.rows.append(row)
        return row

    def mark(self, broker, trade, price, *, partial=False):
        state = self.lots[trade.trade_id]
        value = (price - trade.entry_price) * (1 if trade.size > 0 else -1)
        _update_extrema(state, broker._i, value, -value)
        state["partial"] |= partial

    def before(self, broker, price, phase, conditional):
        self.sample(
            broker,
            price,
            "before_" + phase,
            coverage="partial" if conditional else "complete_under_bar_model",
        )
        for trade in broker.trades:
            self.mark(broker, trade, price, partial=conditional)
        if conditional or phase == "close":
            self.changed_bar = broker._i

    def opened(self, broker, trade, conditional, phase):
        self.lots[trade.trade_id] = {
            "mfe": 0.0,
            "mae": 0.0,
            "mfeBar": broker._i,
            "maeBar": broker._i,
            "partial": conditional,
            "firstFullBar": broker._i + int(conditional or phase != "execute"),
        }

    def close(self, trade, allocation_id):
        self.closed[allocation_id] = self.lots[trade.trade_id].copy()

    def mark_bar(self, broker):
        high, low = (broker._data._current_value(n) for n in ("High", "Low"))
        if high < low:
            high, low = low, high
        for trade in broker.trades:
            state = self.lots[trade.trade_id]
            if state["firstFullBar"] <= broker._i:
                entry = trade.entry_price
                if trade.size > 0:
                    favorable, adverse = high - entry, entry - low
                else:
                    favorable, adverse = entry - low, high - entry
                _update_extrema(state, broker._i, favorable, adverse)
            else:
                self.mark(broker, trade, broker.last_price)

    def bar(self, broker):
        self.mark_bar(broker)
        self.sample(broker, broker.last_price, "bar", range_eligible=self.changed_bar != broker._i)
