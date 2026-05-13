from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from datetime import datetime, timedelta

from marketimmune.schemas.events import AgentOrderEvent


class RollingWindow:
    def __init__(self, horizon: timedelta) -> None:
        self.horizon = horizon
        self.events: deque[AgentOrderEvent] = deque()

    def add(self, event: AgentOrderEvent) -> None:
        self.events.append(event)
        self.evict(event.timestamp)

    def evict(self, now: datetime) -> None:
        cutoff = now - self.horizon
        while self.events and self.events[0].timestamp < cutoff:
            self.events.popleft()

    def snapshot(self) -> list[AgentOrderEvent]:
        return list(self.events)


def windows_for_events(
    events: Iterable[AgentOrderEvent],
    horizons: list[timedelta],
) -> list[dict[str, list[AgentOrderEvent]]]:
    windows = {
        str(int(horizon.total_seconds() * 1000)): RollingWindow(horizon)
        for horizon in horizons
    }
    snapshots: list[dict[str, list[AgentOrderEvent]]] = []
    for event in sorted(events, key=lambda item: item.timestamp):
        for window in windows.values():
            window.add(event)
        snapshots.append({name: window.snapshot() for name, window in windows.items()})
    return snapshots
