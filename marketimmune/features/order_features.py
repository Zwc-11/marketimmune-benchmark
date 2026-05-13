from __future__ import annotations

from statistics import mean

from marketimmune.schemas.events import AgentOrderEvent


def order_features(events: list[AgentOrderEvent]) -> dict[str, float]:
    prices = [event.price for event in events]
    quantities = [event.quantity for event in events]
    buy_count = sum(1 for event in events if event.side == "buy")
    sell_count = len(events) - buy_count
    cancel_count = sum(1 for event in events if event.action == "cancel")
    replace_count = sum(1 for event in events if event.action == "replace")
    fill_count = sum(1 for event in events if event.action == "fill")
    return {
        "order_count": float(len(events)),
        "buy_count": float(buy_count),
        "sell_count": float(sell_count),
        "cancel_count": float(cancel_count),
        "replace_count": float(replace_count),
        "fill_count": float(fill_count),
        "buy_ratio": buy_count / max(len(events), 1),
        "sell_ratio": sell_count / max(len(events), 1),
        "cancel_rate": cancel_count / max(len(events), 1),
        "quantity_sum": sum(quantities),
        "quantity_mean": mean(quantities) if quantities else 0.0,
        "quantity_max": max(quantities, default=0.0),
        "price_mean": mean(prices) if prices else 0.0,
        "price_min": min(prices, default=0.0),
        "price_max": max(prices, default=0.0),
        "price_range": max(prices, default=0.0) - min(prices, default=0.0),
    }
