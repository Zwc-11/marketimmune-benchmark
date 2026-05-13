from __future__ import annotations

from collections.abc import Iterable, Iterator

from marketimmune.schemas.events import CanonicalEvent


class EventCursor:
    def __init__(self, events: Iterable[CanonicalEvent]) -> None:
        self._events = sorted(
            events,
            key=lambda event: (event.timestamp, event.sequence, event.event_id or ""),
        )

    def __iter__(self) -> Iterator[CanonicalEvent]:
        return iter(self._events)

    def __len__(self) -> int:
        return len(self._events)
