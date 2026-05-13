from __future__ import annotations

from marketimmune.schemas.events import AgentOrderEvent


def market_features(events: list[AgentOrderEvent]) -> dict[str, float]:
    if not events:
        return {
            "notional_sum": 0.0,
            "notional_mean": 0.0,
            "aggressive_buy_count": 0.0,
            "aggressive_sell_count": 0.0,
            "price_drift": 0.0,
            "quantity_imbalance": 0.0,
        }
    notionals = [event.price * event.quantity for event in events]
    buys = [event.quantity for event in events if event.side == "buy"]
    sells = [event.quantity for event in events if event.side == "sell"]
    return {
        "notional_sum": sum(notionals),
        "notional_mean": sum(notionals) / len(notionals),
        "aggressive_buy_count": float(sum(1 for event in events if event.side == "buy")),
        "aggressive_sell_count": float(sum(1 for event in events if event.side == "sell")),
        "price_drift": events[-1].price - events[0].price,
        "quantity_imbalance": (sum(buys) - sum(sells)) / max(sum(buys) + sum(sells), 1e-9),
    }
