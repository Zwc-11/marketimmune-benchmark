from __future__ import annotations

from dataclasses import dataclass

from marketimmune.schemas.events import BookTickerEvent, CanonicalEvent, KlineEvent


@dataclass(frozen=True)
class TopOfBook:
    bid_price: float
    bid_quantity: float
    ask_price: float
    ask_quantity: float


class TopNOrderBook:
    def __init__(self, spread_bps: float = 1.0, default_quantity: float = 10.0) -> None:
        self.spread_bps = spread_bps
        self.default_quantity = default_quantity
        self.top: TopOfBook | None = None

    def apply_market_event(self, event: CanonicalEvent) -> TopOfBook | None:
        if isinstance(event, BookTickerEvent):
            self.top = TopOfBook(
                bid_price=event.bid_price,
                bid_quantity=event.bid_quantity,
                ask_price=event.ask_price,
                ask_quantity=event.ask_quantity,
            )
            return self.top
        if not isinstance(event, KlineEvent):
            return self.top
        half_spread = event.close_price * (self.spread_bps / 10_000) / 2
        self.top = TopOfBook(
            bid_price=event.close_price - half_spread,
            bid_quantity=self.default_quantity,
            ask_price=event.close_price + half_spread,
            ask_quantity=self.default_quantity,
        )
        return self.top

    def invariant_bid_below_ask(self) -> bool:
        return self.top is None or self.top.bid_price < self.top.ask_price
