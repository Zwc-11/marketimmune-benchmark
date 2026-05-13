from __future__ import annotations

from dataclasses import dataclass

from marketimmune.replay.order_book import TopOfBook
from marketimmune.schemas.events import AgentOrderEvent, OrderAction


@dataclass(frozen=True)
class Fill:
    order_id: str
    filled_quantity: float
    fill_price: float


class MatchingEngine:
    def match(self, order: AgentOrderEvent, top: TopOfBook | None) -> Fill | None:
        if top is None or order.action != OrderAction.NEW.value:
            return None
        if order.side == "buy" and order.price >= top.ask_price:
            filled = min(order.remaining_quantity, top.ask_quantity)
            return Fill(order.order_id, filled, top.ask_price)
        if order.side == "sell" and order.price <= top.bid_price:
            filled = min(order.remaining_quantity, top.bid_quantity)
            return Fill(order.order_id, filled, top.bid_price)
        return None
