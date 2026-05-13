from __future__ import annotations

from marketimmune.schemas.events import AgentOrderEvent


def agentic_features(events: list[AgentOrderEvent]) -> dict[str, float]:
    if not events:
        return {
            "unique_agents": 0.0,
            "unique_orders": 0.0,
            "orders_per_agent": 0.0,
            "min_interarrival_ms": 0.0,
            "mean_interarrival_ms": 0.0,
            "burst_rate_per_second": 0.0,
            "self_cross_proxy_count": 0.0,
            "opposite_side_same_price_pairs": 0.0,
        }
    agents = {event.agent_id for event in events}
    timestamps = [event.timestamp for event in events]
    deltas = [
        (timestamps[index] - timestamps[index - 1]).total_seconds() * 1000
        for index in range(1, len(timestamps))
    ]
    duration = max((timestamps[-1] - timestamps[0]).total_seconds(), 0.001)
    opposite_pairs = 0
    for index, event in enumerate(events):
        for previous in events[:index]:
            if previous.price == event.price and previous.side != event.side:
                opposite_pairs += 1
    self_cross_proxy = sum(
        1
        for index, event in enumerate(events)
        for previous in events[:index]
        if previous.agent_id == event.agent_id
        and previous.price == event.price
        and previous.side != event.side
    )
    return {
        "unique_agents": float(len(agents)),
        "unique_orders": float(len({event.order_id for event in events})),
        "orders_per_agent": len(events) / max(len(agents), 1),
        "min_interarrival_ms": min(deltas, default=0.0),
        "mean_interarrival_ms": sum(deltas) / len(deltas) if deltas else 0.0,
        "burst_rate_per_second": len(events) / duration,
        "self_cross_proxy_count": float(self_cross_proxy),
        "opposite_side_same_price_pairs": float(opposite_pairs),
    }
