from __future__ import annotations

from marketimmune.replay.matching_engine import Fill, MatchingEngine
from marketimmune.replay.order_book import TopNOrderBook
from marketimmune.schemas.events import AgentOrderEvent, CanonicalEvent


class ShadowBook:
    def __init__(self) -> None:
        self.book = TopNOrderBook()
        self.matcher = MatchingEngine()
        self.seen_order_ids: set[str] = set()
        self.fills: list[Fill] = []

    def apply_market_event(self, event: CanonicalEvent) -> None:
        self.book.apply_market_event(event)

    def apply_agent_order(self, order: AgentOrderEvent) -> Fill | None:
        if order.order_id in self.seen_order_ids:
            raise ValueError(f"duplicate order_id: {order.order_id}")
        self.seen_order_ids.add(order.order_id)
        fill = self.matcher.match(order, self.book.top)
        if fill is not None:
            self.fills.append(fill)
        return fill

    def no_negative_quantity(self) -> bool:
        return all(fill.filled_quantity >= 0 for fill in self.fills)
